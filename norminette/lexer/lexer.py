import re
import string
from typing import Optional, Tuple, cast

from norminette.exceptions import UnexpectedEOF, MaybeInfiniteLoop
from norminette.lexer.dictionary import digraphs, trigraphs
from norminette.lexer.dictionary import brackets
from norminette.lexer.dictionary import keywords
from norminette.lexer.dictionary import operators
from norminette.lexer.tokens import Token
from norminette.file import File
from norminette.errors import Error, Highlight as H


def c(a: str, b: str):
    a = a.lower()
    b = b.lower()
    return (
        a + b, a.upper() + b, a + b.upper(), a.upper() + b.upper(),
        b + a, b.upper() + a, b + a.upper(), b.upper() + a.upper(),
    )


quote_prefixes = (*"lLuU", "u8")
octal_digits = "01234567"
hexadecimal_digits = "0123456789abcdefABCDEF"
integer_suffixes = (
    '',
    *"uUlLzZ",
    "ll", "LL",
    "wb", "WB",
    "i64", "I64",
    *c('u', 'l'),
    *c('u', "ll"),
    *c('u', 'z'),
    *c('u', "wb"),
    *c('u', "i64"),
)
float_suffixes = (
    '',
    *"lLfFdD",
    "dd", "DD",
    "df", "DF",
    "dl", "DL",
    *c('f', 'i'),
    *c('f', 'j'),
)

INT_LITERAL_PATTERN = re.compile(r"""
^
# (?P<Sign>[-+]*)
(?P<Prefix>         # prefix can be
    0[bBxX]*        #   0, 0b, 0B, 0x, 0X, 0bb, 0BB, ...
    |               # or empty
)
(?P<Constant>
    # BUG If prefix is followed by two or more x, it doesn't works correctly
    (?<=0[xX])       # is prefix for hex digits?
        [\da-fA-F]+  #   so, collect hex digits
    |                # otherwise
    \d+              #   collect decimal digits
)
(?P<Suffix>
    (?<=[eE])        # is constant ending with an `E`?
        [\w\d+\-.]*  #   so, collect `+` and `-` operators
    |                # otherwise
        \w           #   collect suffixes that starts with an letter
        [\w\d.]*     #     and letters, digits and dots that follows it
    |                # finally, do suffix be optional (empty)
)
""", re.VERBOSE)


def _float_pattern(const: str, digit: str, exponent: Tuple[str, str]):
    pattern = r"""
    ^
    (?P<Constant>{0})
    (?P<Exponent>
        (?:
        [{2}]+[-+]{3}+
        |[{2}]+{3}+
        |(?:[{2}][+-]?(?:[.{3}]+)?)+
        ){1}
    )
    (?P<Suffix>[\w\d._]*|)
    """.format(const, *exponent, digit)
    return re.compile(pattern, re.VERBOSE)


FLOAT_EXPONENT_LITERAL_PATTERN = _float_pattern(r"\d+", digit=r"\d", exponent=('', "eE"))
FLOAT_FRACTIONAL_LITERAL_PATTERN = _float_pattern(r"(?:\d+)?\.\d+|\d+\.", digit=r"\d", exponent=('?', "eE"))
FLOAT_HEXADECIMAL_LITERAL_PATTERN = _float_pattern(r"0[xX]+[\da-fA-F]+(?:\.[\da-fA-F]+)?",
                                                   digit=r"[\da-fA-F]", exponent=('?', "pP"))


class Lexer:
    def __init__(self, file: File):
        self.file = file

        self.__pos = int(0)
        self.__line_pos = self.__line = 1

    def raw_peek(self, *, offset: int = 0, collect: int = 1):
        if (pos := self.__pos + offset) < len(self.file.source):
            return ''.join(self.file.source[pos:pos+collect])
        return None

    def peek(self, *, times: int = 1, offset: int = 0) -> Optional[Tuple[str, int]]:
        char, size = '', 0
        for _ in range(times):
            if (trigraph := self.raw_peek(offset=offset + size, collect=3)) in trigraphs:
                char += trigraphs[trigraph]
                size += 3
            elif (digraph := self.raw_peek(offset=offset + size, collect=2)) in digraphs:
                char += digraphs[digraph]
                size += 2
            elif word := self.raw_peek(offset=offset + size):
                char += word
                size += 1
            else:
                break
        if size:
            return char, size
        return None  # Let it crash :D

    def pop(
        self,
        *,
        times: int = 1,
        use_spaces: bool = False,
        use_escape: bool = False,
    ) -> str:
        result = ""
        for _ in range(times):
            for _ in range(100):
                if peek := self.peek():
                    char, size = peek
                else:
                    raise UnexpectedEOF()
                if char != '\\':
                    break
                peek = self.peek(offset=size)
                if peek is None:
                    break
                temp, _ = peek  # Don't change the `temp` to `char`
                if temp != '\n':
                    if use_escape:
                        if temp in r"abefnrtv\"'?":
                            size += 1
                            char += temp
                        elif temp == 'x':
                            size += 1
                            char += temp
                            # BUG It is just considering one `byte` (0x0 to 0xFF), so it not works correctly
                            # with prefixed strings like `L"\0x1234"`.
                            peek = self.raw_peek(offset=size, collect=2)
                            if peek is None or peek[0] not in hexadecimal_digits:
                                error = Error.from_name("NO_HEX_DIGITS", level="Notice")
                                error.add_highlight(self.__line, self.__line_pos + size - 1, length=1)
                                self.file.errors.add(error)
                            else:
                                for digit in peek:
                                    if digit not in hexadecimal_digits:
                                        break
                                    size += 1
                                    char += digit
                        elif temp in octal_digits:
                            while (temp := self.raw_peek(offset=size)) and temp in octal_digits:
                                size += 1
                                char += temp
                        else:
                            error = Error.from_name("UNKNOWN_ESCAPE", level="Notice")
                            error.add_highlight(self.__line, self.__line_pos + size, length=1)
                            self.file.errors.add(error)
                            char += temp
                            size += 1
                    break
                self.__pos += size + 1
                self.__line += 1
                self.__line_pos = 0
                peek = self.peek()
                if peek is None:
                    raise UnexpectedEOF()
                char, size = peek
            else:
                # It hits when we have multiple lines followed by `\`, e.g:
                # ```c
                # // hello \
                # a \
                #  b \
                # c\
                # \
                # a
                # ```
                raise MaybeInfiniteLoop()
            if char == '\n':
                self.__line_pos = 0
                self.__line += 1
            if char == '\t':
                self.__line_pos += (spaces := 4 - (self.__line_pos - 1) % 4) - 1
                if use_spaces:
                    char = ' ' * spaces
            self.__line_pos += size
            self.__pos += size
            result += char
        return result

    def line_pos(self):
        return self.__line, self.__line_pos

    def parse_char_literal(self) -> Optional[Token]:
        pos = lineno, column = self.line_pos()
        value = ''
        for prefix in quote_prefixes:
            length = len(prefix)
            result = self.raw_peek(collect=length + 1)
            if not result:
                return
            if result.startswith(prefix) and result.endswith('\''):
                value += self.pop(times=length)
                break
        if self.raw_peek() != '\'':
            return
        chars = 0
        value += self.pop()
        for _ in range(100):
            try:
                char = self.pop(use_escape=True)
            except UnexpectedEOF:
                error = Error.from_name("UNEXPECTED_EOF_CHR", highlights=[
                    H(lineno, column, length=len(value)),
                ])
                self.file.errors.add(error)
                break
            if char == '\n':
                error = Error.from_name("UNEXPECTED_EOL_CHR", highlights=[
                    H(lineno, column, length=len(value)),
                    H(lineno, column + len(value), length=1, hint="Perhaps you forgot a single quote (')?")
                ])
                self.file.errors.add(error)
                break
            value += char
            if char == '\'':
                break
            chars += 1
        else:
            raise MaybeInfiniteLoop()
        if value == "''":
            error = Error.from_name("EMPTY_CHAR", highlights=[H(*pos, length=2)])
            self.file.errors.add(error)
        if chars > 1 and value.endswith('\''):
            error = Error.from_name("CHAR_AS_STRING", highlights=[
                H(*pos, length=len(value)),
                H(*pos, length=1,
                  hint="Perhaps you want a string (double quote, \") instead of a char (single quote, ')?"),
            ])
            self.file.errors.add(error)
        return Token("CHAR_CONST", pos, value=value)

    def parse_string_literal(self):
        """String constants can contain any characer except unescaped newlines.
        An unclosed string or unescaped newline is a fatal error and thus
        parsing will stop here.
        """
        if not self.peek():
            return
        pos = lineno, column = self.line_pos()
        val = ''
        for prefix in quote_prefixes:
            length = len(prefix)
            result = self.raw_peek(collect=length + 1)
            if not result:
                return
            if result.startswith(prefix) and result.endswith('"'):
                val += self.pop(times=length)
                break
        if self.raw_peek() != '"':
            return
        val += self.pop()
        while self.peek() is not None:
            char = self.pop(use_escape=True)
            val += char
            if char == '"':
                break
        else:
            error = Error.from_name("UNEXPECTED_EOF_STR")
            error.add_highlight(*pos, length=len(val))
            error.add_highlight(lineno, column + len(val), length=1, hint="Perhaps you forgot a double quote (\")?")
            self.file.errors.add(error)
        return Token("STRING", pos, val)

    def parse_integer_literal(self):
        # TODO Add to support single quote (') to separate digits according to C23

        match = INT_LITERAL_PATTERN.match(self.file.source[self.__pos:])
        if match is None:
            return

        pos = lineno, column = self.line_pos()
        token = Token("CONSTANT", pos, slice := self.pop(times=match.end()))

        if match["Suffix"] not in integer_suffixes:
            suffix_length = len(match["Suffix"])
            string_length = len(slice) - suffix_length
            if match["Suffix"][0] in "+-":
                error = Error.from_name("MAXIMAL_MUNCH")
                error.add_highlight(lineno, column + string_length, length=1, hint="Perhaps you forgot a space ( )?")
            else:
                error = Error.from_name("INVALID_SUFFIX")
                error.add_highlight(lineno, column + string_length, length=suffix_length)
            self.file.errors.add(error)

        def _check_bad_prefix(name: str, bucket: str):
            error = Error.from_name(f"INVALID_{name}_INT")
            for index, char in enumerate(match["Constant"], start=len(match["Prefix"])):
                if char not in bucket:
                    error.add_highlight(lineno, column + index, length=1)
            if error.highlights:
                self.file.errors.add(error)

        if match["Prefix"] in ("0b", "0B"):
            _check_bad_prefix("BIN", "01")
        elif match["Prefix"] == '0':
            _check_bad_prefix("OCT", "01234567")
        elif match["Prefix"] in ("0x", "0X"):
            _check_bad_prefix("HEX", "0123456789abcdefABCDEF")

        return token

    def parse_float_literal(self):
        """Numeric constants can take many forms:
        - integer constants only allow digits [0-9]
        - real number constant only allow digits [0-9],
            ONE optionnal dot '.' and ONE optionnal 'e/E' character
        - binary constant only allow digits [0-1] prefixed by '0b' or '0B'
        - hex constant only allow digits [0-9], letters [a-f/A-F] prefixed
            by '0x' or '0X'
        - octal constants allow digits [0-9] prefixed by a zero '0'
            character

        Size ('l/L' for long) and sign ('u/U' for unsigned) specifiers can
        be appended to any of those. tokens

        Plus/minus operators ('+'/'-') can prefix any of those tokens

        a numeric constant could start with a '.' (dot character)
        """
        constant = self.raw_peek()
        if constant is None:
            return
        pos = lineno, column = self.line_pos()
        src = self.file.source[self.__pos:]
        if match := FLOAT_EXPONENT_LITERAL_PATTERN.match(src):
            type = "exponent"
        elif match := FLOAT_FRACTIONAL_LITERAL_PATTERN.match(src):
            type = "fractional"
        elif match := FLOAT_HEXADECIMAL_LITERAL_PATTERN.match(src):
            type = "hexadecimal"
        else:
            return
        error = None
        suffix = len(match["Suffix"])
        column += len(match["Constant"])
        badhex = match["Constant"].strip(hexadecimal_digits + '.')
        if type == "exponent" and not re.match(r"[eE][-+]?\d+", match["Exponent"]):
            error = Error.from_name("BAD_EXPONENT")
            error.add_highlight(lineno, column, length=len(match["Exponent"]) + suffix)
        elif type == "hexadecimal" and '.' not in match["Constant"] and not match["Exponent"]:
            return  # Hexadecimal Integer
        elif type == "hexadecimal" and badhex not in ('x', 'X'):
            error = Error.from_name("MULTIPLE_X")
            error.add_highlight(lineno, column - len(match["Constant"]) + 1, length=len(badhex))
        elif match["Constant"].count('.') == 1 and match["Suffix"].count('.') > 0:
            error = Error.from_name("MULTIPLE_DOTS")
            error.add_highlight(lineno, column, length=len(match["Exponent"]) + suffix)
        elif match["Suffix"] not in float_suffixes:
            error = Error.from_name("BAD_FLOAT_SUFFIX")
            error.add_highlight(lineno, column + len(match["Exponent"]), length=suffix)
        if error:
            self.file.errors.add(error)
        return Token("CONSTANT", pos, self.pop(times=match.end()))

    def parse_multi_line_comment(self) -> Optional[Token]:
        if self.raw_peek(collect=2) != "/*":
            return
        pos = lineno, column = self.line_pos()
        val = self.pop(times=2)
        eof = False
        while self.peek():
            try:
                val += self.pop(use_spaces=True)
            except UnexpectedEOF:
                eof = True
                break
            if val.endswith("*/"):
                break
        else:
            eof = True
        if eof:
            # TODO Add a better highlight since it is a multi-line token
            error = Error.from_name("UNEXPECTED_EOF_MC")
            error.add_highlight(lineno, column, length=len(val))
            self.file.errors.add(error)
        return Token("MULT_COMMENT", pos, val)

    def parse_line_comment(self) -> Optional[Token]:
        """Comments are anything after '//' characters, up until a newline or
        end of file
        """
        if self.raw_peek(collect=2) != "//":
            return
        pos = self.line_pos()
        val = self.pop(times=2)
        while result := self.peek():
            char, _ = result
            if char == '\n':
                break
            try:
                val += self.pop()
            except UnexpectedEOF:
                break
        return Token("COMMENT", pos, val)

    def parse_identifier(self) -> Optional[Token]:
        """Identifiers can start with any letter [a-z][A-Z] or an underscore
        and contain any letters [a-z][A-Z] digits [0-9] or underscores
        """
        char = self.raw_peek()
        if not char or char not in string.ascii_letters + '_':
            return
        pos = self.line_pos()
        val = self.pop()
        while char := self.raw_peek():
            if char not in string.ascii_letters + "0123456789_":
                break
            val += self.pop()
        if val in keywords:
            return Token(keywords[val], pos)
        return Token("IDENTIFIER", pos, val)

    def parse_operator(self):
        """Operators can be made of one or more sign, so the longest operators
        need to be looked up for first in order to avoid false positives
        eg: '>>' being understood as two 'MORE_THAN' operators instead of
            one 'RIGHT_SHIFT' operator
        """
        result = self.peek()
        if not result:
            return
        char, _ = result
        if char not in "+-*/,<>^&|!=%;:.~?#":
            return
        pos = self.line_pos()
        if char in ".+-*/%<>^&|!=":
            if self.raw_peek(collect=3) in (">>=", "<<=", "..."):
                return Token(operators[self.pop(times=3)], pos)
            temp, _ = self.peek(times=2)  # type: ignore
            if temp in (">>", "<<", "->"):
                return Token(operators[self.pop(times=2)], pos)
            if temp == char + "=":
                return Token(operators[self.pop(times=2)], pos)
            if char in "+-<>=&|":
                if temp == char * 2:
                    return Token(operators[self.pop(times=2)], pos)
        char = self.pop()
        return Token(operators[char], pos)

    def parse_whitespace(self) -> Optional[Token]:
        char = self.raw_peek()
        if char is None or char not in "\n\t ":
            return
        if char == ' ':
            token = Token("SPACE", self.line_pos())
        elif char == "\t":
            token = Token("TAB", self.line_pos())
        elif char == "\n":
            token = Token("NEWLINE", self.line_pos())
        self.pop()
        return token

    def parse_brackets(self) -> Optional[Token]:
        result = self.peek()
        if result is None:
            return
        char, _ = result
        if char not in brackets:
            return
        start = self.line_pos()
        value = self.pop()
        return Token(brackets[value], start, value=value)

    parsers = (
        parse_float_literal,  # Need to be above:
                              #  `parse_operator` to avoid `<DOT>`
                              #  `parse_integer_literal` to avoid `\d+`
        parse_integer_literal,
        parse_char_literal,
        parse_string_literal,
        parse_identifier,  # Need to be bellow `char` and `string`
        parse_whitespace,
        parse_line_comment,
        parse_multi_line_comment,
        parse_operator,
        parse_brackets,
    )

    def get_next_token(self) -> Optional[Token]:
        """Peeks one character and tries to match it to a token type,
        if it doesn't match any of the token types, an error will be raised
        and current file's parsing will stop
        """
        while self.raw_peek():
            if self.raw_peek(collect=2) == "\\\n" or self.raw_peek(collect=4) == "??/\n":
                # Avoid using `.pop()` here since it ignores the escaped
                # newline and pops and upcomes after it. E.g, if we have
                # `\\\nab` and use `.pop()`, the parsers funcs will see `b``.
                _, size = self.peek()  # type: ignore
                self.__pos += cast(int, size) + 1
                self.__line += 1
                self.__line_pos = 1
            else:
                break
        for parser in self.parsers:
            if result := parser(self):
                return result
        if char := self.raw_peek():
            error = Error("BAD_LEXEME", f"No matchable token for '{char}' lexeme")
            error.add_highlight(*self.line_pos(), length=1)
            self.file.errors.add(error)
            self.__pos += 1
            self.__line_pos += 1
            # BUG If we have multiples bad lexemes, it can raise RecursionError
            return self.get_next_token()

    def __iter__(self):
        while token := self.get_next_token():
            yield token

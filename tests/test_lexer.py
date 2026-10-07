from itertools import chain
from typing import Dict, Any, List, Optional, Tuple

import pytest

from norminette.lexer import Token as T
from norminette.lexer.dictionary import keywords, operators, brackets
from norminette.errors import Error as E, Highlight as H
from norminette.exceptions import UnexpectedEOF
from tests.utils import (
    dict_to_pytest_param,
    lexer_from_source,
)


@pytest.mark.parametrize("source, parameters, expected", dict_to_pytest_param({
    "No args": ["oi", {}, 'o'],
    "Empty source": ['', {}, None],
    "Collect over than source length": ["hello", {"collect": 10}, "hello"],
    "Collect with empty source": ['', {"collect": 3}, None],
    "Offset in empty source": ['', {"offset": 3}, None],
    "Offset": ["Hello", {"offset": 2}, 'l'],
    "Offset with collect": ["Hello, world!", {"offset": 7, "collect": 5}, "world"],
    "Offset over than source length with collect": ["Hello, world!", {"offset": 14, "collect": 3}, None],
    "Newline": ["\naa", {}, '\n'],
    "Escaped newline": ["\\\n", {}, '\\'],
}))
def test_lexer_raw_peek(source: str, parameters: Dict[str, Any], expected: Optional[str]):
    lexer = lexer_from_source(source)

    assert lexer.raw_peek(**parameters) == expected


@pytest.mark.parametrize("source, parameters, expected", dict_to_pytest_param({
    "Single source char": ['{', {}, ('{', 1)],
    "Single digraph source": ["<%", {}, ('{', 2)],
    "Single trigraph source": ["??<", {}, ('{', 3)],
    "Newline": ['\n', {}, ('\n', 1)],
    "Escaped newline": ["\\\n", {}, ('\\', 1)],
    "Times with exact chars": ["abc", {"times": 3}, ("abc", 3)],
    "Times with trigraphs": [r"??<a??<b", {"times": 4}, ("{a{b", 8)],
    "Times with trigraphs 2": [r"??<a??<b", {"times": 4}, ("{a{b", 8)],
    "Offset with large source": ["heello!s", {"offset": 6}, ('!', 1)],
    # "Offset with large source with trigraphs": ["he??<el??/lo!s", {"offset": 8}, ('!', 1)],  # teoric BUG
    "Empty source": ['', {}, None],
    "Offset over source length": ["abc", {"offset": 3}, None],
    "Offset to last char": ["abc", {"offset": 2}, ('c', 1)],
    "Offset with times": ["abc", {"offset": 1, "times": 2}, ("bc", 2)],
    "Offset with times and digraphs": ["hey<%wa<%ts", {"offset": 2, "times": 5}, ("y{wa{", 7)],
    # "Offset with times and trigraphs": ["??/hey<%wa<%ts", {"offset": 1, "times": 4}, ("hey{", 5)],  # teoric BUG
}))
def test_lexer_peek(source: str, parameters: Dict[str, Any], expected: Optional[Tuple[str, int]]):
    lexer = lexer_from_source(source)

    assert lexer.peek(**parameters) == expected


@pytest.mark.parametrize("source, parameters, expected", dict_to_pytest_param({
    "Empty source": ['', {}, None],
    "One letter source": ['a', {}, 'a'],
    "Two letter source": ["ab", {}, 'a'],
    "Times with no source length": ['a', {"times": 2}, None],
    "Times with large source length": ["abc", {"times": 2}, "ab"],
    "Times with exact source length": ["abc", {"times": 3}, "abc"],
    "Tab": ["\t 2", {}, '\t'],
    "Tab with use_spaces": ["\t 2", {"use_spaces": True}, "    "],
    "Tab with use_spaces and times": ["\t 2", {"use_spaces": True, "times": 3}, "     2"],
    "Tab in second column with use_spaces and times": ["ch\t2", {"use_spaces": True, "times": 4}, "ch  2"],
    "Newline followed by a letter": ["\na", {}, '\n'],
    "Newline with times": ["\nab", {"times": 2}, "\na"],
    "Escaped newline in EOF": ["\\\n", {}, None],
    "Escaped newline in SOF": ["\\\nabc", {}, 'a'],
    "Escaped newline with times": ["a\\\nbc", {"times": 2}, "ab"],
    "Backslash followed by a escaped newline with times": ["\\\\\nab", {"times": 2}, r"\a"],
    "Escaped single quote without use_escape": [r"\'", {}, '\\'],
    "Escaped single quote with use_escape": [r"\'", {"use_escape": True}, r"\'"],
    "Escaped newline without use_escape": [r"\n", {}, '\\'],
    "Escaped newline with use_escape": [r"\'", {"use_escape": True}, r"\'"],
    "Twice escaped single quote with times but without use_escape": [r"\'\'", {"times": 4}, r"\'\'"],
    "String with escaped single quote twice with times but without use_escape": ["\"\\'\\'\"", {"times": 6},
                                                                                 "\"\\'\\'\""],
    "String with escaped single quote twice with times and use_escape": ["\"\\'\\'\"",
                                                                         {"times": 4, "use_escape": True},
                                                                         "\"\\'\\'\""],
    "Char containing newline with times and use_escape": [r"'\n'", {"times": 3, "use_escape": True}, r"'\n'"],
    "Use trigraph instead of backslash to escape single quote": ["??/'", {"use_escape": True}, r"\'"],
    "Use trigraph to escape newline with times": ["a??/\nb", {"times": 2, "use_escape": True}, r"ab"],
    "Multiples escaped newlines": ["\\\n\\\na\n", {}, 'a'],
    "Multiples escaped newlines with trigraphs": ["??/\n??/\na\n", {}, 'a'],
    "Bla": ["\\\na\n", {}, 'a'],
    "Escape hex followed by EOF": [r"\x", {}, '\\'],
    "Escape hex followed by EOF with use_escape": [r"\x", {"use_escape": True}, r"\x"],
    "Bad escape hex with use_escape and times": [r"\x\x", {"use_escape": True, "times": 2}, r"\x\x"],
    "Ok escape hex followed by a bad with use_escape and times": [r"\xF\x", {"use_escape": True, "times": 2}, r"\xF\x"],
}))
def test_lexer_pop(source: str, parameters: Dict[str, Any], expected: Optional[str]):
    lexer = lexer_from_source(source)

    if expected is None:
        pytest.raises(UnexpectedEOF, lexer.pop, **parameters)
    else:
        assert lexer.pop(**parameters) == expected


@pytest.mark.parametrize("source, str_expected, errors", dict_to_pytest_param({
    "Unexpected EOF only quote": ['\'', "<CHAR_CONST='>", [
        E.from_name("UNEXPECTED_EOF_CHR", highlights=[H(lineno=1, column=1, length=1)])
    ]],
    "Unexpected EOF with quote and letter": ["'a", "<CHAR_CONST='a>", [
        E.from_name("UNEXPECTED_EOF_CHR", highlights=[H(lineno=1, column=1, length=2)]),
    ]],
    "Unexpected EOF with char as string": ["'Farofa ", "<CHAR_CONST='Farofa >", [
        E.from_name("UNEXPECTED_EOF_CHR", highlights=[H(lineno=1, column=1, length=len("'Farofa "))]),
    ]],
    "Unexpected EOL only quote": ["'\n", "<CHAR_CONST='>", [
        E.from_name("UNEXPECTED_EOL_CHR", highlights=[
            H(lineno=1, column=1, length=1),
            H(lineno=1, column=1 + len("'"), length=1, hint="Perhaps you forgot a single quote (')?"),
        ]),
    ]],
    "Unexpected EOL with quote and letter": ["'a\n", "<CHAR_CONST='a>", [
        E.from_name("UNEXPECTED_EOL_CHR", highlights=[
            H(lineno=1, column=1, length=2),
            H(lineno=1, column=1 + len("'a"), length=1, hint="Perhaps you forgot a single quote (')?"),
        ]),
    ]],
    "Unexpected EOL with char as string": ["'Astronauta\n", "<CHAR_CONST='Astronauta>", [
        E.from_name("UNEXPECTED_EOL_CHR", highlights=[
            H(lineno=1, column=1, length=len("'Astronauta")),
            H(lineno=1, column=1 + len("'Astronauta"), length=1, hint="Perhaps you forgot a single quote (')?"),
        ]),
    ]],
    "ASCII letter": ["'a'", "<CHAR_CONST='a'>", []],
    "ASCII number": ["'9'", "<CHAR_CONST='9'>", []],
    "Single quote escaped": [r"'\''", r"<CHAR_CONST='\''>", []],
    "Newline": [r"'\n'", r"<CHAR_CONST='\n'>", []],
    "Empty char": ["''", "<CHAR_CONST=''>", [
        E.from_name("EMPTY_CHAR", highlights=[H(lineno=1, column=1, length=2)])],
    ],
    "String quote": ['"a"', "None", []],
    "Int literal": ['1', "None", []],
    "Null": [r"'\0'", r"<CHAR_CONST='\0'>", []],
    "Hexadecimal char E9 (é)": [r"'\xE9'", R"<CHAR_CONST='\xE9'>", []],
    "Hexadecimal char without sequence": [r"'\x'", R"<CHAR_CONST='\x'>", [
        E.from_name("NO_HEX_DIGITS", level="Notice", highlights=[
            H(lineno=1, column=3, length=1),
        ]),
    ]],
    "Escape sequence that doesn't exists": [r"'\j'", r"<CHAR_CONST='\j'>", [
        E.from_name("UNKNOWN_ESCAPE", level="Notice", highlights=[
            H(lineno=1, column=3, length=1),
        ]),
    ]],
    "Char too long": ["'John Galt'", "<CHAR_CONST='John Galt'>", [
        E.from_name("CHAR_AS_STRING", highlights=[
            H(lineno=1, column=1, length=len("'John Galt'")),
            H(lineno=1, column=1, length=1,
              hint="Perhaps you want a string (double quote, \") instead of a char (single quote, ')?"),
        ])
    ]],
    "Char with L prefix": ["L'a'", "<CHAR_CONST=L'a'>", []],
    "Char escaped with L prefix": [r"L'\n'", r"<CHAR_CONST=L'\n'>", []],
    "Hex with one digit": [r"'\xA'", r"<CHAR_CONST='\xA'>", []],
    "Hex with two digits": [r"'\x3F'", r"<CHAR_CONST='\x3F'>", []],
    "U prefixed char": ["U'h'", "<CHAR_CONST=U'h'>", []],
    "u8 prefixed char": ["u8'h'", "<CHAR_CONST=u8'h'>", []],
    "Bad prefixed char": ["s'h'", "None", []],
}))
def test_lexer_parse_char_literal(source: str, str_expected: str, errors: List[E]):
    lexer = lexer_from_source(source)
    token = lexer.parse_char_literal()

    assert str(token) == str_expected
    assert repr(lexer.file.errors) == repr(errors)


@pytest.mark.parametrize("source, str_expected, errors", dict_to_pytest_param({
    "Empty string": ["\"\"", "<STRING=\"\">", []],
    "ASCII normal string": ["\"x+1=2, where x=1\"", "<STRING=\"x+1=2, where x=1\">", []],
    "Single quote string": ["'teste'", "None", []],
    "Unexpected EOF with empty string": ['\"', "<STRING=\">", [
        E.from_name("UNEXPECTED_EOF_STR", highlights=[
            H(lineno=1, column=1, length=1),
            H(lineno=1, column=2, length=1, hint="Perhaps you forgot a double quote (\")?"),
        ]),
    ]],
    "Unexpected EOF": ['\"asd', "<STRING=\"asd>", [
        E.from_name("UNEXPECTED_EOF_STR", highlights=[
            H(lineno=1, column=1, length=4),
            H(lineno=1, column=5, length=1, hint="Perhaps you forgot a double quote (\")?"),
        ]),
    ]],
    "String with escaped new line": ["\"first\\\n second\"", "<STRING=\"first second\">", []],
    "Basic string": ["\"Basic string\"", "<STRING=\"Basic string\">", []],
    "L basic string": ["L\"Basic string\"", "<STRING=L\"Basic string\">", []],
    "U prefixed string": ["U\"hIGH\"", "<STRING=U\"hIGH\">", []],
    "u8 prefixed string": ["u8\"hIGH\"", "<STRING=u8\"hIGH\">", []],
    "Bad prefixed string": ["s\"hIGH\"", "None", []],
    "String with escaped quotes": ["\"Basic \\\"string\\\"\"", "<STRING=\"Basic \\\"string\\\"\">", []],
    "Multiples escapes and escaped quote": [r'"Escaped \\\"string\\\\\"\\"',
                                            r'<STRING="Escaped \\\"string\\\\\"\\">',
                                            []],
}))
def test_lexer_parse_string_literal(source: str, str_expected: str, errors: List[E]):
    lexer = lexer_from_source(source)
    token = lexer.parse_string_literal()

    assert str(token) == str_expected
    assert repr(lexer.file.errors) == repr(errors)


@pytest.mark.parametrize("source, str_expected", dict_to_pytest_param({
    "Empty comment": ["//", "<COMMENT=//>"],
    "Comment at EOF": ["// The sky is falling", "<COMMENT=// The sky is falling>"],
    "Comment at EOL": ["// The sky is falling\n", "<COMMENT=// The sky is falling>"],
    "Comment with escaped line in EOF": ["// The sky is falling\\", r"<COMMENT=// The sky is falling\>"],
    "Comment with escaped line in EOF using trigraph": [r"// The sky is falling??/",
                                                        r"<COMMENT=// The sky is falling\>"],
    "Comment with escaped line": ["// The sky is falling\\\n!", "<COMMENT=// The sky is falling!>"],
    "Comment with escaped line using trigraph": ["// The sky is falling??/\n!", "<COMMENT=// The sky is falling!>"],
}))
def test_lexer_parse_line_comment(source: str, str_expected: str):
    lexer = lexer_from_source(source)
    token = lexer.parse_line_comment()

    assert str(token) == str_expected
    assert lexer.file.errors.status == "OK"


@pytest.mark.parametrize("source, str_expected, errors", dict_to_pytest_param({
    "Multi-line comment in single line at EOF": ["/* The sky is falling*/",
                                                 "<MULT_COMMENT=/* The sky is falling*/>", []],
    "Multi-line comment in multiples lines at EOF": ["/*\na\nb\n\n\n*/", "<MULT_COMMENT=/*\na\nb\n\n\n*/>", []],
    "Multi-line comment with escaped line": ["/*\\\na*/", "<MULT_COMMENT=/*a*/>", []],
    "Multi-line comment with escaped line using trigraph": ["/*??/\na*/", "<MULT_COMMENT=/*a*/>", []],
    "Multi-line comment not terminated with escaped line before EOF": ["/*\\\n", "<MULT_COMMENT=/*>", [
        E.from_name("UNEXPECTED_EOF_MC", highlights=[
            H(lineno=1, column=1, length=len("/*")),
        ]),
    ]],
    "Multi-line comment not terminated": ["/* uepaaa\ne agora??", "<MULT_COMMENT=/* uepaaa\ne agora??>", [
        E.from_name("UNEXPECTED_EOF_MC", highlights=[
            H(lineno=1, column=1, length=len("/* uepaaa\ne agora??")),
        ]),
    ]],
    "Multi-line comment not terminate ending with a backslash": ["/*\\", r"<MULT_COMMENT=/*\>", [
        E.from_name("UNEXPECTED_EOF_MC", highlights=[
            H(lineno=1, column=1, length=len("/*\\")),
        ]),
    ]],
    "Comment (not multi-line)": ["// hey, i'm not a multi-line comment", "None", []],
    "Space before a multi-line comment": [" /* */", "None", []],
}))
def test_lexer_parse_multi_line_comment(source: str, str_expected: str, errors: List[E]):
    lexer = lexer_from_source(source)
    token = lexer.parse_multi_line_comment()

    assert str(token) == str_expected
    assert repr(lexer.file.errors) == repr(errors)


@pytest.mark.parametrize("source, str_expected, errors", dict_to_pytest_param({
    "Decimal integer": ["1234567890", "<CONSTANT=1234567890>", []],
    "Decimal integer with UL as suffix": ["1234567890UL", "<CONSTANT=1234567890UL>", []],
    "Decimal integer with bad suffix": ["1234567890ABC", "<CONSTANT=1234567890ABC>", [
        E.from_name("INVALID_SUFFIX", highlights=[
            H(lineno=1, column=11, length=len("ABC")),
        ]),
    ]],
    "Binary integer": ["0b1101011", "<CONSTANT=0b1101011>", []],
    "Binary integer with U as suffix": ["0b000001U", "<CONSTANT=0b000001U>", []],
    "Binary integer with bad digits": ["0b1210491011", "<CONSTANT=0b1210491011>", [
        E.from_name("INVALID_BIN_INT", highlights=[
            H(lineno=1, column=4, length=1, hint=None),  # 2
            H(lineno=1, column=7, length=1, hint=None),  # 4
            H(lineno=1, column=8, length=1, hint=None),  # 9
        ]),
    ]],
    "Binary with bad suffix": ["0b0101e", "<CONSTANT=0b0101e>", [
        E.from_name("INVALID_SUFFIX", highlights=[H(lineno=1, column=7, length=1)]),
    ]],
    "Octal integer": ["01234567123", "<CONSTANT=01234567123>", []],
    "Octal integer with U as suffix": ["0123u", "<CONSTANT=0123u>", []],
    "Octal integer with bad digits": ["00072189", "<CONSTANT=00072189>", [
        E.from_name("INVALID_OCT_INT", highlights=[
            H(lineno=1, column=7, length=1, hint=None),  # 8
            H(lineno=1, column=8, length=1, hint=None),  # 9
        ]),
    ]],
    "Octal integer with bad suffix with dots": ["000123u.23", "<CONSTANT=000123u.23>", [
        E.from_name("INVALID_SUFFIX", highlights=[
            H(lineno=1, column=len("000123") + 1, length=len("u.23")),
        ]),
    ]],
    "Hexadecimal with bad suffix": ["0x1uLl;", "<CONSTANT=0x1uLl>", [
        E.from_name("INVALID_SUFFIX", highlights=[H(lineno=1, column=4, length=3)]),
    ]],
    "Integer with u suffix": ["123u", "<CONSTANT=123u>", []],
    "Integer with U suffix": ["123U", "<CONSTANT=123U>", []],
    "Integer with uz suffix": ["123uz", "<CONSTANT=123uz>", []],
    "Integer with UZ suffix": ["123UZ", "<CONSTANT=123UZ>", []],
    "Integer with z suffix": ["123z", "<CONSTANT=123z>", []],
    "Integer with Z suffix": ["123Z", "<CONSTANT=123Z>", []],
    "Integer with ul suffix": ["123ul", "<CONSTANT=123ul>", []],
    "Integer with UL suffix": ["123UL", "<CONSTANT=123UL>", []],
    "Integer with ull suffix": ["123ull", "<CONSTANT=123ull>", []],
    "Integer with ULL suffix": ["123ULL", "<CONSTANT=123ULL>", []],
    "Integer with ll suffix": ["9000000000ll", "<CONSTANT=9000000000ll>", []],
    "Integer with LL suffix": ["9000000000LL", "<CONSTANT=9000000000LL>", []],
    "Integer with bad suffix": ["10Uu", "<CONSTANT=10Uu>", [
        E.from_name("INVALID_SUFFIX", highlights=[H(lineno=1, column=3, length=len("10"))]),
    ]],
}))
def test_lexer_parse_integer_literal(source: str, str_expected: str, errors: List[E]):
    lexer = lexer_from_source(source)
    token = lexer.parse_integer_literal()

    assert str(token) == str_expected
    assert repr(lexer.file.errors) == repr(errors)


@pytest.mark.parametrize("source, str_expected, errors", dict_to_pytest_param({
    "Integer": ["1234567890", "None", []],
    "Integer with exponent-part": ["1e2", "<CONSTANT=1e2>", []],
    "Integer with exponent-part and f as suffix": ["1e2f", "<CONSTANT=1e2f>", []],
    "Integer with bad exponent-part": ["1eeee2xf", "<CONSTANT=1eeee2xf>", [
        E.from_name("BAD_EXPONENT", highlights=[H(lineno=1, column=2, length=7)]),
    ]],
    "Exponent with sign": ["1e+3", "<CONSTANT=1e+3>", []],
    "Bad float followed by an unary expression": ["45e++ai", "<CONSTANT=45e+>", [
        E.from_name("BAD_EXPONENT", highlights=[H(lineno=1, column=3, length=2)]),
    ]],
    "Identifier with numbers": ["e42", "None", []],
    "Fractional exponent with bad suffix": [".0e4x;", "<CONSTANT=.0e4x>", [
        E.from_name("BAD_FLOAT_SUFFIX", highlights=[H(lineno=1, column=5, length=1)]),
    ]],
    "Integer with bad suffix": ["10uu", "None", []],
    "Bad suffix with all parts": ["10.12fe10", "<CONSTANT=10.12fe10>", [
        E.from_name("BAD_FLOAT_SUFFIX", highlights=[H(lineno=1, column=6, length=len("fe10"))]),
    ]],
    "Float without fractional part but with suffix": ["10.f", "<CONSTANT=10.f>", []],
    "Float without fractional part but bad suffix": ["10.fU", "<CONSTANT=10.fU>", [
        E.from_name("BAD_FLOAT_SUFFIX", highlights=[H(lineno=1, column=4, length=2)]),
    ]],
    "Real bad suffix": ["21.3E56E4654", "<CONSTANT=21.3E56E4654>", [
        E.from_name("BAD_FLOAT_SUFFIX", highlights=[H(lineno=1, column=8, length=5)]),
    ]],
    "Exponent with D suffix": ["105e4d", "<CONSTANT=105e4d>", []],
    "Bad exponent followed by a suffix": ["105eu", "<CONSTANT=105eu>", [
        E.from_name("BAD_EXPONENT", highlights=[H(lineno=1, column=4, length=2)]),
    ]],
    "Multiple dots": ["1.1..2.3.4.5", "<CONSTANT=1.1..2.3.4.5>", [
        E.from_name("MULTIPLE_DOTS", highlights=[H(lineno=1, column=4, length=len("..2.3.4.5"))]),
    ]],
    "Hexadecimal multiple dots": ["0xF.22..2.3.4.5", "<CONSTANT=0xF.22..2.3.4.5>", [
        E.from_name("MULTIPLE_DOTS", highlights=[H(lineno=1, column=7, length=len("..2.3.4.5"))]),
    ]],
    "Hexadecimal with just constant": ["0xC0FFE", "None", []],
    "Hexadecimal integer with suffix": ["0XA0000024u", "None", []],
    "Hexadecimal integer with double suffix": ["0XA0000021uL", "None", []],
    "Multiple X": ["0xxXxxX123.32f", "<CONSTANT=0xxXxxX123.32f>", [
        E.from_name("MULTIPLE_X", highlights=[H(lineno=1, column=2, length=len("xxXxxX"))]),
    ]],
    "Multiple X in an integer hexadecimal": ["0xX1", "None", []],
    "Multiple X with exponent": ["0xxAp2", "<CONSTANT=0xxAp2>", [
        E.from_name("MULTIPLE_X", highlights=[H(lineno=1, column=2, length=2)]),
    ]],
    **{
        # https://www.gnu.org/software/c-intro-and-ref/manual/html_node/Floating-Constants.html
        f"Float GNU {number} {source!r}": [source, f"<CONSTANT={source}>", []]
        for number, source in enumerate((
            "1500.0", "15e2", "15e+2", "15.0e2", "1.5e+3", ".15e4", "15000e-1",
            "1.0", "1000.", "3.14159", ".05", ".0005", "1e0", "1.0000e0", "100e1",
            "100e+1", "100E+1", "1e3", "10000e-1", "3.14159e0", "5e-2", ".0005e+2",
            "5E-2", ".0005E2", ".05e-2", "3.14159f", "3.14159e0f", "1000.f", "100E1F",
            ".0005f", ".05e-2f",
            "0xAp2", "0xAp-1", "0x2.0Bp4", "0xE.2p3", "0x123.ABCp0",
            "0x123.ABCp4", "0x100p-8", "0x10p-4", "0x1p+4", "0x1p+8",
        ))
    }
}))
def test_lexer_parse_float_literal(source: str, str_expected: str, errors: List[E]):
    lexer = lexer_from_source(source)
    token = lexer.parse_float_literal()

    assert str(token) == str_expected
    assert repr(lexer.file.errors) == repr(errors)


@pytest.mark.parametrize("source, str_expected", dict_to_pytest_param({
    "Identifier starting with an integer": ["42_hello", "None"],
    "Identifier starting with an underscore": ["_hello", "<IDENTIFIER=_hello>"],
    "ft_printf identifier": ["ft_printf", "<IDENTIFIER=ft_printf>"],
    "Identifier with just underscore": ['_', "<IDENTIFIER=_>"],
    "Identifier with just one letter": ['a', "<IDENTIFIER=a>"],
    "Identifier with uppercase letters": ["EGGS", "<IDENTIFIER=EGGS>"],
    "Identifier with mixedcase letters": ["AbCd", "<IDENTIFIER=AbCd>"],
    "Identifier with lowercase letters": ["duck", "<IDENTIFIER=duck>"],
    "Identifier with an hyphen": ["clojure-is-cool", "<IDENTIFIER=clojure>"],
    "Identifier with integers, letters and underscores": ["ascii_2_bigint128", "<IDENTIFIER=ascii_2_bigint128>"],
    "String starting with an letter": ["L\"ola\"", "<IDENTIFIER=L>"],
    "Char starting with an letter": ["L'1'", "<IDENTIFIER=L>"],
}))
def test_lexer_parse_identifier(source: str, str_expected: str):
    lexer = lexer_from_source(source)
    token = lexer.parse_identifier()

    assert str(token) == str_expected
    assert lexer.file.errors.status == "OK"


@pytest.mark.parametrize("keyword", keywords.keys())
def test_lexer_parse_identifier_keyword_only(keyword: str):
    lexer = lexer_from_source(keyword)
    token = lexer.parse_identifier()

    assert str(token) == f"<{keywords[keyword]}>"
    assert lexer.file.errors.status == "OK"


@pytest.mark.parametrize("operator, token_type", list(operators.items()) + [
    ["??=", "HASH"],
    ["%:", "HASH"],
    ["??'", "BWISE_XOR"],
    ["??'=", "XOR_ASSIGN"],
    ["??!", "BWISE_OR"],
    ["??!??!", "OR"],
    ["??!=", "OR_ASSIGN"],
    ["??-", "BWISE_NOT"],
])
def test_lexer_parse_operator(operator: str, token_type: str):
    lexer = lexer_from_source(operator)
    token = lexer.parse_operator()

    assert str(token) == f"<{token_type}>"
    assert lexer.file.errors.status == "OK"


@pytest.mark.parametrize("bracket, token_type", list(brackets.items()) + [
    ["<%", "LBRACE"],
    ["??<", "LBRACE"],
    ["%>", "RBRACE"],
    ["??>", "RBRACE"],
    ["<:", "LBRACKET"],
    ["??(", "LBRACKET"],
    [":>", "RBRACKET"],
    ["??)", "RBRACKET"],
])
def test_lexer_parse_brackets(bracket: str, token_type: str):
    lexer = lexer_from_source(bracket)
    token = lexer.parse_brackets()

    assert str(token) == f"<{token_type}>"
    assert lexer.file.errors.status == "OK"


@pytest.mark.parametrize("source, expected_tokens", dict_to_pytest_param({
    "Empty source": ['', []],
    "Just space source": ["   ", [
        T("SPACE", (1, 1)),
        T("SPACE", (1, 2)),
        T("SPACE", (1, 3)),
    ]],
    "Identifier followed by a comment": ["test//comment", [
        T("IDENTIFIER", (1, 1), "test"),
        T("COMMENT", (1, 5), "//comment"),
    ]],
    "Main function prototype with void": ["int\tmain(void);", [
        T("INT", (1, 1)),
        T("TAB", (1, 4)),
        T("IDENTIFIER", (1, 5), value="main"),
        T("LPARENTHESIS", (1, 9)),
        T("VOID", (1, 10)),
        T("RPARENTHESIS", (1, 14)),
        T("SEMI_COLON", (1, 15)),
    ]],
    # Checks if `identifier` is bellow to `char` and `string`
    "Wide char/string followed by identifier": ["L'a' L\"bcd\" name", [
        T("CHAR_CONST", (1, 1), value="L'a'"),
        T("SPACE", (1, 5)),
        T("STRING", (1, 6), value="L\"bcd\""),
        T("SPACE", (1, 12)),
        T("IDENTIFIER", (1, 13), value="name"),
    ]],
    "Integer": ["42", [T("CONSTANT", (1, 1), value="42")]],
    "Integer with plus sign": ["+42", [
        T("PLUS", (1, 1)),
        T("CONSTANT", (1, 2), value="42"),
    ]],
    "Integer with minus sign": ["-42", [
        T("MINUS", (1, 1)),
        T("CONSTANT", (1, 2), value="42"),
    ]],
    "Integer with double sign": ["+-42", [
        T("PLUS", (1, 1)),
        T("MINUS", (1, 2)),
        T("CONSTANT", (1, 3), value="42"),
    ]],
    "Float": ["4.2", [T("CONSTANT", (1, 1), value="4.2")]],
    "Float without integer part": [".42", [T("CONSTANT", (1, 1), value=".42")]],
    "Float exponential": ["4e2", [T("CONSTANT", (1, 1), value="4e2")]],
    "Float with exponential in fractional part without integer": [".4e2", [T("CONSTANT", (1, 1), value=".4e2")]],
    "Float exponential with suffix": ["4e2f", [T("CONSTANT", (1, 1), value="4e2f")]],
    "Float exponential in fractional part with suffix": [".4e2f", [T("CONSTANT", (1, 1), value=".4e2f")]],
    "Octal": ["042", [T("CONSTANT", (1, 1), value="042")]],
    "Hexadecimal": ["0x42", [T("CONSTANT", (1, 1), value="0x42")]],
    "Negative hexadecimal": ["-0x4e2", [
        T("MINUS", (1, 1)),
        T("CONSTANT", (1, 2), value="0x4e2"),
    ]],
    "Integer with l as suffix": ["42l", [T("CONSTANT", (1, 1), value="42l")]],
    "Integer with ul as suffix": ["42ul", [T("CONSTANT", (1, 1), value="42ul")]],
    "Integer with ll as suffix": ["42ll", [T("CONSTANT", (1, 1), value="42ll")]],
    "Integer with ull as suffix": ["42ull", [T("CONSTANT", (1, 1), value="42ull")]],
    "Integer with u suffix": ["42u", [T("CONSTANT", (1, 1), value="42u")]],
    "Multiples signs": ["-+-+-+-+-+-+-+-0Xe4Ae2", [
        T("MINUS", (1, 1)),
        T("PLUS", (1, 2)),
        T("MINUS", (1, 3)),
        T("PLUS", (1, 4)),
        T("MINUS", (1, 5)),
        T("PLUS", (1, 6)),
        T("MINUS", (1, 7)),
        T("PLUS", (1, 8)),
        T("MINUS", (1, 9)),
        T("PLUS", (1, 10)),
        T("MINUS", (1, 11)),
        T("PLUS", (1, 12)),
        T("MINUS", (1, 13)),
        T("PLUS", (1, 14)),
        T("MINUS", (1, 15)),
        T("CONSTANT", (1, 16), value="0Xe4Ae2"),
    ]],
    "Member expression with left part": [".e42", [
        T("DOT", (1, 1)),
        T("IDENTIFIER", (1, 2), value="e42")
    ]],
    "Multiples dots in float": ["4.4.4", [T("CONSTANT", (1, 1), value="4.4.4")]],
    "Multiples exponents": ["4e4e4", [T("CONSTANT", (1, 1), value="4e4e4")]],
    "Bad suffix 1": ["4x4x4", [T("CONSTANT", (1, 1), value="4x4x4")]],
    "Bad suffix 2": ["42uul", [T("CONSTANT", (1, 1), value="42uul")]],
    "Bad suffix 3": ["42Lllu", [T("CONSTANT", (1, 1), value="42Lllu")]],
    "Bad suffix 4": ["42lul", [T("CONSTANT", (1, 1), value="42lul")]],
    "Bad exponent": [".42e", [T("CONSTANT", (1, 1), ".42e")]],
    "Escaped newline followed by an identifier": ["\\\nhello;", [
        T("IDENTIFIER", (2, 1), value="hello"),
        T("SEMI_COLON", (2, 6)),
    ]],
    # TODO Add tests for digraphs/trigraphs
    **dict(chain.from_iterable(map(dict.items, (
        {
            f"Empty {name}": [f"#{name}", [
                T("HASH", (1, 1)),
                T("IDENTIFIER", (1, 2), value=name),
            ]],
            f"Empty spaced {name}": [f"# {name} ", [
                T("HASH", (1, 1)),
                T("SPACE", (1, 2)),
                T("IDENTIFIER", (1, 3), value=name),
                T("SPACE", (1, 3 + len(name))),
            ]],
            f"Empty {name} ending with withespaces": [f"#{name} 	", [
                T("HASH", (1, 1)),
                T("IDENTIFIER", (1, 2), value=name),
                T("SPACE", (1, 2 + len(name))),
                T("TAB", (1, 3 + len(name))),
            ]],
            f"Empty {name} ending with a comment separated by space": [f"#{name} //bla", [
                T("HASH", (1, 1)),
                T("IDENTIFIER", (1 , 2), value=name),
                T("SPACE", (1, 2 + len(name))),
                T("COMMENT", (1, 3 + len(name)), value="//bla"),
            ]],
            f"Empty {name} followed by a comment": [f"#{name}//bla ", [
                T("HASH", (1, 1)),
                T("IDENTIFIER", (1, 2), value=name),
                T("COMMENT", (1, 2 + len(name)), value="//bla "),
            ]],
        }
        for name in ("define", "error", "ifndef", "ifdef", "include", "pragma", "undef")
    )))),
}))
def test_lexer_tokens(source: str, expected_tokens: List[T]):
    lexer = lexer_from_source(source)
    tokens = list(lexer)

    assert tokens == expected_tokens

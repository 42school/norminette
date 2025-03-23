import sys
import contextlib

from norminette.rules import Rule, Primary
from norminette.lexer.dictionary import keywords
from norminette.exceptions import CParsingError
from norminette.context import Macro

UNARY_OPERATORS = (
    "PLUS",
    "MINUS",
    "NOT",  # !
    "BWISE_NOT",  # ~
)

BINARY_OPERATORS = (
    # Arithmetic operators
    "PLUS",
    "MINUS",
    "MULT",
    "DIV",
    "MODULO",
    # Relational operators
    "EQUALS",  # ==
    "NOT_EQUAL",  # !=
    "MORE_THAN",  # > (why not GREATER_THAN?)
    "LESS_THAN",  # <
    "GREATER_OR_EQUAL",  # >=
    "LESS_OR_EQUAL",  # <=
    # Logical operators
    "AND",
    "OR",
    # Bitwise operators
    "BWISE_AND",  # &
    "BWISE_OR",  # |
    "BWISE_XOR",  # ^
    "BWISE_XOR",  # ^
    "LEFT_SHIFT",  # << (why not BWISE_LEFT?)
    "RIGHT_SHIFT",  # >>
)

ALLOWED_IN_PATH = (
    "IDENTIFIER",
    "DIV",
    "MINUS",
    "DOT",
    "SPACE",
    "TAB",
    # TODO Remove all keyword tokens and add to just use 'IDENTIFIER' instead
    *keywords.values(),  # https://github.com/42School/norminette/issues/470
)


@contextlib.contextmanager
def recursion_limit(limit):
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(limit)
    yield
    sys.setrecursionlimit(old_limit)


class IsPreprocessorStatement(Rule, Primary, priority=100):
    def run(self, context):
        """
        Catches any kind of preprocessor statements
        Handles indentation related informations
        """
        i = context.skip_ws(0)
        if not context.check_token(i, "HASH"):
            return False, 0
        self.hash = context.peek_token(i)
        i += 1
        i = context.skip_ws(i)
        if context.check_token(i, "NEWLINE"):  # Null directive
            return True, i + 1                 # TODO: Fix null directives (comments)
        # Why `if` and `else` need to be a special case?
        if not context.check_token(i, ("IDENTIFIER", "IF", "ELSE")):
            raise CParsingError(f"Invalid preprocessor statement {context.peek_token(i)}")
        token = context.peek_token(i)
        direc = (token.value if token.type == "IDENTIFIER" else token.type).lower()
        i += 1
        i = context.skip_ws(i)
        if checker := getattr(self, f"check_{direc}", None):
            return checker(context, i)
        raise CParsingError(f"Invalid preprocessing directive #{direc}")

    def check_define(self, context, index):
        if not context.check_token(index, "IDENTIFIER"):
            raise CParsingError("No identifier after #define")
        token = context.peek_token(index)
        index += 1
        if is_function := context.check_token(index, "LPARENTHESIS"):
            index += 1
            index = context.skip_ws(index)
            while context.check_token(index, "IDENTIFIER"):
                index += 1
                index = context.skip_ws(index)
                if context.check_token(index, "COMMA"):
                    index += 1
                    index = context.skip_ws(index)
            # Add better errors like check EOF and invalid identifier?
            if not context.check_token(index, "RPARENTHESIS"):
                raise CParsingError("Invalid macro function definition")
            index += 1
        macro = Macro.from_token(token, is_func=is_function)
        context.preproc.macros.append(macro)
        index = context.skip_ws(index)
        return self._just_token_string("define", context, index)

    def check_import(self, context, index):
        is_valid_argument, index = self._check_path(context, index)
        if not is_valid_argument:
            raise CParsingError("Invalid file argument for #import directive")
        index = context.skip_ws(index)
        return self._just_token_string("import", context, index)

    def check_pragma(self, context, index):
        return self._just_token_string("pragma", context, index)

    def check_error(self, context, index):
        return self._just_token_string("error", context, index)

    def check_warning(self, context, index):
        return self._just_token_string("warning", context, index)

    def check_if(self, context, index):
        if not self.corresponding_endif(context, index):
            context.new_error("PREPROC_BAD_IF", self.hash)
        context.preproc.indent += 1
        context.preproc.total_ifs += 1
        return self._just_constant_expression("if", context, index)

    def check_elif(self, context, index):
        if not self.corresponding_endif(context, index):
            context.new_error("PREPROC_BAD_ELIF", self.hash)
        context.preproc.total_elifs += 1
        return self._just_constant_expression("elif", context, index)

    def check_ifdef(self, context, index):
        if not self.corresponding_endif(context, index):
            context.new_error("PREPROC_BAD_IFDEF", self.hash)
        context.preproc.indent += 1
        context.preproc.total_ifdefs += 1
        return self._just_identifier("ifdef", context, index)

    def check_ifndef(self, context, index):
        if not self.corresponding_endif(context, index):
            context.new_error("PREPROC_BAD_IFNDEF", self.hash)
        context.preproc.indent += 1
        context.preproc.total_ifndefs += 1
        return self._just_identifier("infdef", context, index)

    def check_undef(self, context, index):
        return self._just_identifier("undef", context, index)

    def check_else(self, context, index):
        if context.preproc.indent == 0:
            context.new_error("PREPROC_BAD_ELSE", self.hash)
        context.preproc.total_elses += 1
        return self._just_eol("else", context, index)

    def check_endif(self, context, index):
        if context.preproc.indent == 0:
            context.new_error("PREPROC_BAD_ENDIF", self.hash)
        context.preproc.indent -= 1
        return self._just_eol("endif", context, index)

    def check_include(self, context, index):
        is_valid_argument, index = self._check_path(context, index)
        if not is_valid_argument:
            raise CParsingError("Invalid file argument for #include directive")
        return self._just_eol("include", context, index)

    def corresponding_endif(self, context, index):
        """Checks if the corresponding `#endif` is present.
        """
        depth = 0
        while index < len(context.tokens):
            if not context.check_token(index, "HASH"):
                index += 1
                continue

            index += 1
            index = context.skip_ws(index)
            if not context.check_token(index, ("IDENTIFIER", "IF", "ELSE")):
                continue

            token = context.peek_token(index)
            direc = (token.value if token.type == "IDENTIFIER" else token.type).lower()
            if direc == "endif":
                if depth == 0:
                    return True
                depth -= 1
            elif direc in ("if", "ifdef", "ifndef"):
                depth += 1
            index += 1
        return False

    def _check_path(self, context, index):
        """Checks the argument of an include/import statement.

        Examples of valid headers:
        - `"libft.h"`
        - `<    bla.h   >`
        - `<42.h   >`
        - `<   four.two>`
        """
        # TODO: It not works with `#include <if.h>` because of the `if` keyword
        if context.check_token(index, "STRING"):
            index += 1
            return True, index
        if not context.check_token(index, "LESS_THAN"):
            return False, index
        index = context.skip_ws(index + 1)
        while context.check_token(index, ALLOWED_IN_PATH):
            index += 1
        if not context.check_token(index, "MORE_THAN"):
            return False, index
        index += 1
        return True, index

    def _just_token_string(self, directive, context, index):
        index = context.skip_ws(index, comment=True)
        if context.check_token(index, "NEWLINE"):
            index += 1
            return True, index
        lines = 1
        newline = False
        while context.peek_token(index) is not None and lines > 0:
            if context.check_token(index, "NEWLINE"):
                lines -= 1
                newline = False
            elif context.check_token(index, "BACKSLASH") and not newline:
                lines += 1
                newline = True
            index += 1
        if lines > 0 and context.peek_token(index) is not None:
            raise CParsingError(f"Unexpected end of file after #{directive} directive")
        return True, index

    def _just_constant_expression(self, directive, context, index):
        parser = ConstantExpressionParser(directive, context, index)
        ok, index = parser.parse()
        if not ok:
            return ok, index
        return self._just_eol(directive, context, index)

    def _just_identifier(self, directive, context, index):
        if not context.check_token(index, "IDENTIFIER"):
            raise CParsingError(f"Invalid argument for #{directive} statement")
        index += 1
        return self._just_eol(directive, context, index)

    def _just_eol(self, directive, context, index):
        index = context.skip_ws(index, comment=True)
        if context.peek_token(index) is None:
            return True, index
        #     raise CParsingError(f"Unexpected end of file after #{directive} directive")
        if not context.check_token(index, "NEWLINE"):
            raise CParsingError(f"Extra tokens at end of #{directive} directive")
        index += 1
        return True, index


class ConstantExpressionParser:
    """Parses a constant expression that can be used in preprocessor statements.

    ```bnf
    <expression> ::= <term>
            | unary_operator <expression>
            | ( "(" <expression> ")" | <expression> ) ( binary_operator <expression> )*
    <term> ::= string
            | constant
            | identifier
            | identifier '(' [ <expression> ("," <expression> )* ] ')'
    ```
    The `string`, `constant` and `identifier` comes from the tokenizer.
    """

    def __init__(self, directive, context, index):
        self.directive = directive
        self.context = context
        self.index = index

    def parse(self):
        try:
            index = self.index
            self.parse_constant_expression()
            if index == self.index:  # No tokens were parsed
                raise CParsingError(f"No argument for #{self.directive} statement")
            if self.context.peek_token(self.index) is None:
                raise CParsingError("Unexpected end of file while parsing constant expression")
            self.index = self.context.skip_ws(self.index, comment=True)
            if not self.context.check_token(self.index, "NEWLINE"):
                raise CParsingError("Unexpected tokens after the constant expression")
            # self.index += 1  # Skip the newline
        except RecursionError:
            raise CParsingError("Constant expression too complex")
        return True, self.index

    def skip_ws(self):
        self.index = self.context.skip_ws(self.index)

    @recursion_limit(100)
    def parse_constant_expression(self):
        self.parse_expression()

    def parse_expression(self):
        if self.context.check_token(self.index, "LPARENTHESIS"):
            self.index += 1
            self.parse_expression()
            if not self.context.check_token(self.index, "RPARENTHESIS"):
                raise CParsingError("Missing closing parenthesis while parsing constant expression")
            self.index += 1
            self.parse_potential_binary_operator()
            return

        if (
                self.context.check_token(self.index, UNARY_OPERATORS)
                or (
                    self.context.check_token(self.index, "IDENTIFIER")
                    and self.context.peek_token(self.index).value == "defined"
                )
        ):
            self.index += 1
            self.skip_ws()
            self.parse_expression()
            return

        if self.context.check_token(self.index, "IDENTIFIER"):
            self.index += 1
            if self.context.check_token(self.index, "LPARENTHESIS"):
                self.index += 1
                self.parse_function_macro()
                return
            self.parse_potential_binary_operator()
            return

        if self.context.check_token(self.index, ("STRING", "CONSTANT", "CHAR_CONST")):
            self.index += 1
            self.parse_potential_binary_operator()
            return

    def parse_function_macro(self):
        self.skip_ws()
        if not self.context.check_token(self.index, "RPARENTHESIS"):
            self.parse_expression()
            while self.context.check_token(self.index, "COMMA"):
                self.index += 1
                self.skip_ws()
                self.parse_expression()
        if not self.context.check_token(self.index, "RPARENTHESIS"):
            raise CParsingError("Missing closing parenthesis")
        self.index += 1
        self.skip_ws()

    def parse_potential_binary_operator(self):
        self.skip_ws()
        if self.context.check_token(self.index, BINARY_OPERATORS):
            self.index += 1
            self.skip_ws()
            self.parse_expression()
            return

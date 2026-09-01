from norminette.rules import Rule, Check
from norminette.exceptions import CParsingError


operators = [
    "RIGHT_ASSIGN",
    "LEFT_ASSIGN",
    "ADD_ASSIGN",
    "SUB_ASSIGN",
    "MUL_ASSIGN",
    "DIV_ASSIGN",
    "MOD_ASSIGN",
    "AND_ASSIGN",
    "XOR_ASSIGN",
    "OR_ASSIGN",
    "LESS_OR_EQUAL",
    "GREATER_OR_EQUAL",
    "EQUALS",
    "NOT_EQUAL",
    "ASSIGN",
    "SEMI_COLON",
    "DOT",
    "NOT",
    "MINUS",
    "PLUS",
    "MULT",
    "DIV",
    "MODULO",
    "LESS_THAN",
    "MORE_THAN",
    "PTR",
    "AND",
    "OR",
    "BWISE_XOR",
    "BWISE_OR",
    "BWISE_NOT",
    "BWISE_AND",
    "RIGHT_SHIFT",
    "LEFT_SHIFT",
]

nest_kw = ["RPARENTHESIS", "LPARENTHESIS", "NEWLINE"]


class CheckAssignationIndent(Rule, Check):
    depends_on = (
        "IsAssignation",
        "IsFuncPrototype",
        "IsFunctionCall",
        "IsVarDeclaration",
    )

    def run(self, context):
        """
        Declared variables must be aligned using tabs with other variables on the same scope
        """
        i = 0
        expected = context.scope.indent
        if context.history[-1] in ["IsAssignation", "IsVarDeclaration"]:
            nest = expected + 1
        elif context.history[-1] == "IsFuncPrototype":
            nest = context.func_alignment
        else:
            nest = expected
        while context.check_token(i, ["SEMI_COLON"]) is False:
            if context.check_token(i, "NEWLINE") is True:
                if context.check_token(i - 1, operators) is True:
                    context.new_error("EOL_OPERATOR", context.peek_token(i))
                tmp = context.skip_ws(i + 1)
                if context.check_token(tmp, "COMMA"):
                    context.new_error("COMMA_START_LINE", context.peek_token(i))
                got = 0
                i += 1
                while context.check_token(i + got, "TAB") is True:
                    got += 1
                if context.peek_token(i + got) is None:
                    raise CParsingError(
                        f"Error: Unexpected EOF l.{context.peek_token(i - 1).pos[0]}"
                    )
                # A closing brace goes back a level, and so does an opening
                # one alone on its line, which opens a block. One that starts
                # an element of an initialiser does not: the norm wants the
                # block indented
                dedent = context.check_token(i + got, ["RBRACKET", "RBRACE"]) is True
                if context.check_token(i + got, ["LBRACKET", "LBRACE"]) is True:
                    tmp = context.skip_ws(i + got + 1)
                    dedent = context.check_token(tmp, "NEWLINE") is True
                if dedent:
                    nest -= 1
                if got > nest or (
                    got > nest + 1
                    and context.history[-1] in ["IsAssignation", "IsVarDeclaration"]
                ):
                    context.new_error("TOO_MANY_TAB", context.peek_token(i))
                elif got < nest or (
                    got < nest - 1
                    and context.history[-1] in ["IsAssignation", "IsVarDeclaration"]
                ):
                    context.new_error("TOO_FEW_TAB", context.peek_token(i))
                if dedent:
                    nest += 1
            if context.check_token(i, "LPARENTHESIS") is True:
                nest += 1
            if context.check_token(i, "RPARENTHESIS") is True:
                nest -= 1
            i += 1
        return False, 0

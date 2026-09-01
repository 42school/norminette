import math
import string

from norminette.rules import Rule, Check


keywords = [
    # C reserved keywords #
    "AUTO",
    "BREAK",
    "CASE",
    "CHAR",
    "CONST",
    "CONTINUE",
    "DEFAULT",
    "DO",
    "DOUBLE",
    "ELSE",
    "ENUM",
    "EXTERN",
    "FLOAT",
    "FOR",
    "GOTO",
    "IF",
    "INT",
    "LONG",
    "REGISTER",
    "RETURN",
    "SHORT",
    "SIGNED",
    "SIZEOF",
    "STATIC",
    "STRUCT",
    "SWITCH",
    "TYPEDEF",
    "UNION",
    "UNSIGNED",
    "VOID",
    "VOLATILE",
    "WHILE",
    "IDENTIFIER",
]
qualifiers = [
    "CONST",
    "VOLATILE",
]
assigns_or_eol = [
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
    "ASSIGN",
    "SEMI_COLON",
    "NEWLINE",
    "COMMA",
]


class CheckVariableIndent(Rule, Check):
    depends_on = (
        "IsVarDeclaration",
    )

    def check_tabs(self, context):
        i = 0
        current_indent = context.scope.indent
        type_identifier_nb = -1
        has_tab = False
        line_start = True
        id_length = 0
        buffer_len = 0
        nests = ["LPARENTHESIS", "LBRACE", "LBRACKET"]
        depth = 0
        while context.check_token(i, assigns_or_eol) is False:
            # `void\t(*const f)(int)`: the qualifier is not a type word
            if context.check_token(i, keywords) is True and not (
                depth > 0
                and context.check_token(i, qualifiers) is True
            ):
                type_identifier_nb += 1
            if (
                context.check_token(i, nests)
                and type_identifier_nb > 0
                and context.parenthesis_contain(i)[0] != "pointer"
            ):
                i = context.skip_nest(i)
            elif context.check_token(i, nests) is True:
                depth += 1
            elif context.check_token(i, ["RPARENTHESIS", "RBRACE", "RBRACKET"]) is True:
                depth -= 1
            i += 1
        i = 0
        while context.check_token(i, assigns_or_eol) is False:
            if context.check_token(i, "LBRACKET") is True:
                while context.check_token(i, "RBRACKET") is False:
                    if context.check_token(i, "SIZEOF") is True:
                        i += 1
                        i = context.skip_nest(i)
                        continue
                    elif context.check_token(i, "IDENTIFIER") is True:
                        if context.peek_token(i).value in context.enum_constants:
                            i += 1
                            continue
                        for c in context.peek_token(i).value:
                            if c in string.ascii_lowercase:
                                context.new_error(
                                    "VLA_FORBIDDEN", context.peek_token(i)
                                )
                                break
                        return True, i
                    i += 1
            if context.check_token(i, keywords) is True and type_identifier_nb > 0:
                line_start = False
                type_identifier_nb -= 1
                if context.peek_token(i).length == 0:
                    id_length = len(str(context.peek_token(i))) - 2
                else:
                    id_length = context.peek_token(i).length
                current_indent += math.floor((id_length + buffer_len) / 4)
                buffer_len = 0
            elif context.check_token(i, "SPACE") is True and type_identifier_nb > 0:
                buffer_len += 1
            elif context.check_token(i, "TAB") is False and type_identifier_nb == 0:
                context.new_error("SPACE_REPLACE_TAB", context.peek_token(i))
                return True, i
            elif context.check_token(i, "TAB") is True and type_identifier_nb == 0:
                has_tab += 1
                current_indent += 1
                type_identifier_nb -= 1
            elif (
                context.check_token(i, "TAB")
                and type_identifier_nb > 0
                and line_start is False
            ):
                context.new_error("TAB_REPLACE_SPACE", context.peek_token(i))
            i += 1
        return False, 0

    def run(self, context):
        """
        Each variable must be indented at the same level for its scope
        """
        i = 0
        identifier = None
        ident = [0, 0]
        ret = None
        self.check_tabs(context)
        while (
            context.peek_token(i)
            and context.check_token(i, ["SEMI_COLON", "COMMA", "ASSIGN"]) is False
        ):
            if context.check_token(i, ["LBRACKET", "LBRACE"]) is True:
                i = context.skip_nest(i)
            if context.check_token(i, "LPARENTHESIS") is True:
                ret, _ = context.parenthesis_contain(i)
            if context.check_token(i, "IDENTIFIER") is True:
                ident = (context.peek_token(i), i)
                if ret == "pointer":
                    break
            i += 1
        i = ident[1]
        identifier = ident[0]
        if context.check_token(i - 1, ["MULT", "BWISE_AND", "LPARENTHESIS"]) is True:
            i -= 1
            while (
                context.check_token(i - 1, ["MULT", "BWISE_AND", "LPARENTHESIS"])
                is True
                and context.is_operator(i) is False
            ):
                i -= 1
            identifier = context.peek_token(i)
        if context.scope.vars_alignment == 0:
            context.scope.vars_alignment = identifier.pos[1]
        elif context.scope.vars_alignment != identifier.pos[1]:
            context.new_error("MISALIGNED_VAR_DECL", context.peek_token(i))
            return True, i
        return False, 0

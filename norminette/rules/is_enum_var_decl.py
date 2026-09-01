from norminette.rules import Rule, Primary
from norminette.scope import UserDefinedEnum


lbrackets = ["LBRACE", "LPARENTHESIS", "LBRACKET"]
rbrackets = ["RBRACE", "RPARENTHESIS", "RBRACKET"]


class IsEnumVarDecl(Rule, Primary, priority=30):
    scope = (
        UserDefinedEnum,
    )

    def assignment_right_side(self, context, pos):
        sep = ["COMMA", "ASSIGN", "NEWLINE"]
        i = context.skip_ws(pos, nl=True)
        while context.peek_token(i) and context.check_token(i, sep) is False:
            if context.check_token(i, lbrackets) is True:
                i = context.skip_nest(i)
            i += 1
        return True, i

    def var_declaration(self, context, pos):
        brackets = 0
        parenthesis = 0
        braces = 0
        i = pos
        identifier = False
        while (
            context.peek_token(i) is not None
            and context.check_token(i, ["COMMA", "RBRACE", "NEWLINE"]) is False
        ):
            if (
                context.check_token(i, "IDENTIFIER") is True
                and braces == 0
                and brackets == 0
                and parenthesis == 0
            ):
                identifier = True
                context.enum_constants.add(context.peek_token(i).value)
            elif context.check_token(i, ["COMMENT", "MULT_COMMENT"]) is True:
                i += 1
                continue
            elif context.check_token(i, lbrackets) is True:
                if context.check_token(i, "LBRACE") is True:
                    braces += 1
                if context.check_token(i, "LBRACKET") is True:
                    brackets += 1
                if context.check_token(i, "LPARENTHESIS") is True:
                    parenthesis += 1
            elif context.check_token(i, rbrackets) is True:
                if context.check_token(i, "RBRACE") is True:
                    braces -= 1
                if context.check_token(i, "RBRACKET") is True:
                    brackets -= 1
                if context.check_token(i, "RPARENTHESIS") is True:
                    parenthesis -= 1
            elif context.check_token(i, "ASSIGN") is True:
                if identifier is False:
                    return False, pos
                ret, i = self.assignment_right_side(context, i + 1)
                i -= 1
                if ret is False:
                    return False, pos
            elif context.check_token(
                i, ["SPACE", "TAB", "MULT", "BWISE_AND", "NEWLINE"]
            ):
                pass
            elif parenthesis == 0 and brackets == 0 and braces == 0:
                return False, 0
            i += 1
        if identifier is False:
            return False, pos
        if context.check_token(i, ["NEWLINE", "COMMA"]) is True:
            return True, i
        return False, pos

    def run(self, context):
        """
        Enum have special var declarations so this catches these specific variables
        """
        ret, i = self.var_declaration(context, 0)
        if ret is False:
            return False, 0
        while ret:
            ret, i = self.var_declaration(context, i)
            if context.check_token(i, ["COMMA"]) is True:
                i += 1
                i = context.eol(i)
                return True, i
            elif context.check_token(i, ["NEWLINE"]) is True:
                i = context.eol(i)
                return True, i
        return False, 0

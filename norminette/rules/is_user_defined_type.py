from norminette.rules import Rule, Primary
from norminette.scope import UserDefinedType, UserDefinedEnum

utypes = ["TYPEDEF", "UNION", "STRUCT", "ENUM"]


class IsUserDefinedType(Rule, Primary, priority=45):
    def typedef(self, context, pos):
        i = context.skip_ws(pos)
        if "TYPEDEF" not in [tkn.type for tkn in context.tokens[:i]]:
            return False, pos
        ret, i = context.check_identifier(i)
        if ret is False:
            i += 1
            if context.check_token(i, "LBRACE"):
                return True, i
            return False, pos
        i += 1
        return True, i

    def utype_definition(self, context, pos):
        utypes = ["STRUCT", "ENUM", "UNION"]
        if not [tkn for tkn in context.tokens[:pos] if tkn.type in utypes]:
            return False, pos
        return True, pos

    def run(self, context):
        """
        Catches user type definitions
        Can include the whole type definition in case it's a structure
        Variable declarations aren't included
        """
        i = context.skip_ws(0, nl=False)
        enum = False
        p = 0
        ids = []
        while context.peek_token(i) is not None:
            if context.check_token(i, utypes) is True and p <= 0:
                break
            if context.check_token(i, "LPARENTHESIS") is True:
                p += 1
            if context.check_token(i, "RPARENTHESIS") is True:
                p -= 1
            if context.check_token(i, ["NEWLINE", "SEMI_COLON"]) is True:
                return False, 0
            i += 1
        if context.peek_token(i) is None:
            return False, 0
        p = 0
        b = 0
        while context.peek_token(i):
            if context.check_token(i, "LPARENTHESIS") is True:
                p += 1
            if context.check_token(i, "RPARENTHESIS") is True:
                p -= 1
            if context.check_token(i, "LBRACKET") is True:
                b += 1
            if context.check_token(i, "RBRACKET") is True:
                b -= 1
            if context.check_token(i, "ENUM") is True:
                enum = True
            if context.check_token(i, ["NEWLINE", "SEMI_COLON"]) is True and p == 0:
                break
            # `typedef char t_buf[LEN];`: an array size is not the type name
            if context.check_token(i, "IDENTIFIER") and b == 0:
                ids.append(context.peek_token(i))
            i += 1
        if context.check_token(i, "NEWLINE") is True and p <= 0:
            if enum is True:
                context.sub = context.scope.inner(UserDefinedEnum)
            else:
                context.sub = context.scope.inner(UserDefinedType)
            i = context.eol(i)
            return True, i
        elif context.check_token(i, "SEMI_COLON") is True:
            i += 1
            if ids:
                context.scope.vars_name.append(ids[-1])
            i = context.eol(i)
            return True, i

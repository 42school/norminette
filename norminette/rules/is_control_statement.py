from norminette.context import ControlStructure
from norminette.scope import Function
from norminette.context import GlobalScope
from norminette.rules import Rule, Primary

cs_keywords = [
    "DO",
    "WHILE",
    "FOR",
    "IF",
    "ELSE",
    "SWITCH",
    "CASE",
    "DEFAULT",
    "IDENTIFIER",
]
whitespaces = ["TAB", "SPACE", "NEWLINE"]


class IsControlStatement(Rule, Primary, priority=65):
    scope = (
        Function,
        ControlStructure,
        GlobalScope,
    )

    def run(self, context):
        """
        Catches control statements, including for/switch
        Includes the condition, even if over multiple lines
        """
        is_id = False
        id_instead_cs = False
        i = context.skip_ws(0, nl=False)
        if context.check_token(i, cs_keywords) is False:
            return False, 0
        keyword = context.peek_token(i).type
        if context.check_token(i, "IDENTIFIER") is True:
            is_id = True
            id_instead_cs = True
        if context.check_token(i, ["SWITCH", "CASE", "DEFAULT"]) is True:
            i += 1
            i = context.skip_ws(i, nl=False)
            if context.check_token(i, "LPARENTHESIS") is True:
                i = context.skip_nest(i)
            i = context.skip_ws(i, nl=False)
            if context.check_token(i, ["CONSTANT", "IDENTIFIER"]) is True:
                i += 1
            i = context.skip_ws(i, nl=False)
            context.sub = context.scope.inner(ControlStructure)
            context.sub.multiline = False
            context.sub.keyword = keyword
            if context.check_token(i, "COLON") is True:
                i += 1
                i = context.eol(i)
                return True, i
            else:
                while context.check_token(i, ["LBRACE", "NEWLINE"]) is False:
                    i += 1
                i = context.eol(i)
                return True, i
        if context.check_token(i, "ELSE") is True:
            i += 1
            while context.check_token(i, ["TAB", "SPACE"]) is True:
                i += 1
            if context.check_token(i, "SEMI_COLON") is True:
                i += 1
                i = context.eol(i)
                return True, i
            if context.check_token(i, "NEWLINE") is True:
                context.sub = context.scope.inner(ControlStructure)
                context.sub.multiline = False
                context.sub.keyword = keyword
                i = context.eol(i)
                return True, i
            if context.check_token(i, ["IF"]) is True:
                keyword = "IF"
            elif context.check_token(i, ["LBRACE", "COMMENT", "MULT_COMMENT"]) is False:
                context.sub = context.scope.inner(ControlStructure)
                context.sub.multiline = False
                context.sub.keyword = keyword
                i = context.eol(i)
                return True, i
            else:
                context.sub = context.scope.inner(ControlStructure)
                context.sub.multiline = False
                context.sub.keyword = keyword
                i = context.eol(i)
                return True, i
        i += 1
        if id_instead_cs is True:
            return False, 0
        i = context.skip_ws(i, nl=False)
        if context.check_token(i, "LPARENTHESIS") is False:
            return False, 0
        i = context.skip_nest(i)
        i += 1
        tmp = context.skip_ws(i, nl=True)
        if context.check_token(tmp, "SEMI_COLON") is True:
            if is_id is True:
                return False, 0
            tmp += 1
            tmp = context.eol(tmp)
            return True, tmp
        i = context.skip_ws(i, nl=False)
        context.sub = context.scope.inner(ControlStructure)
        context.sub.multiline = False
        context.sub.keyword = keyword
        i = context.eol(i)
        return True, i

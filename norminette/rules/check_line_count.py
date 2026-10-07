from norminette.context import GlobalScope
from norminette.rules import Rule, Check


class CheckLineCount(Rule, Check):
    def run(self, context):
        """
        Each function can only have 25 lines between its opening and closing brackets
        """
        # Count the physical lines the statement spans: a string or a comment
        # can swallow newlines of its own, and they are lines all the same
        tokens = context.tokens[: context.tkn_scope]
        if tokens:
            context.scope.lines += tokens[-1].lineno - tokens[0].lineno
            if tokens[-1].type in ("NEWLINE", "ESCAPED_NEWLINE"):
                context.scope.lines += 1

        if type(context.scope) is GlobalScope:

            if context.get_parent_rule() == "CheckFuncDeclarations" and context.scope.lines > 25:
                context.new_error("TOO_MANY_LINES", context.tokens[context.tkn_scope])
            return False, 0

        if context.get_parent_rule() == "CheckBrace":
            if "LBRACE" in [t.type for t in context.tokens[: context.tkn_scope + 1]]:
                if type(context.scope) is GlobalScope:
                    return False, 0
            else:
                if context.scope.lvl == 0:
                    return False, 0

        return False, 0

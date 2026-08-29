from norminette.rules import Rule, Check


class CheckTernary(Rule, Check):
    def is_define(self, context):
        """
        Returns True if the current statement is a `#define` directive.
        """
        i = context.skip_ws(0)
        if not context.check_token(i, "HASH"):
            return False
        i = context.skip_ws(i + 1)
        if not context.check_token(i, "IDENTIFIER"):
            return False
        return context.peek_token(i).value == "define"

    def run(self, context):
        """
        Ternaries are forbidden
        """
        if context.preproc.skip_define and self.is_define(context):
            return
        for i in range(0, context.tkn_scope):
            if context.check_token(i, "TERN_CONDITION") is True:
                context.new_error("TERNARY_FBIDDEN", context.peek_token(i))
        return False, 0

from norminette.rules import Rule, Check

names = ("typeof", "__typeof__", "typeof_unqual")


class CheckTypeof(Rule, Check):
    def run(self, context):
        """
        typeof is forbidden
        """
        for i in range(0, context.tkn_scope):
            if context.check_token(i, "IDENTIFIER") is not True:
                continue
            if context.peek_token(i).value not in names:
                continue
            if context.check_token(context.skip_ws(i + 1), "LPARENTHESIS"):
                context.new_error("TYPEOF_FORBIDDEN", context.peek_token(i))
        return False, 0

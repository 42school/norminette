from norminette.rules import Rule, Check


class CheckLineLen(Rule, Check):
    def run(self, context):
        """
        Lines must not be over 80 characters long
        """
        for tkn in context.tokens[: context.tkn_scope]:
            if tkn.pos[1] > 81 and tkn.pos[0] not in context.errors.lines_with("LINE_TOO_LONG"):
                context.new_error("LINE_TOO_LONG", tkn)
        return False, 0

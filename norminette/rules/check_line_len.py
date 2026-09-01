from norminette.rules import Rule, Check


class CheckLineLen(Rule, Check):
    def run(self, context):
        """
        Lines must not be over 80 characters long
        """
        reported = {
            highlight.lineno
            for error in context.errors
            if error.name == "LINE_TOO_LONG"
            for highlight in error.highlights
        }
        for tkn in context.tokens[: context.tkn_scope]:
            if tkn.pos[1] > 81 and tkn.pos[0] not in reported:
                context.new_error("LINE_TOO_LONG", tkn)
                reported.add(tkn.pos[0])
        return False, 0

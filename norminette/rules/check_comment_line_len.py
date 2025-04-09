from norminette.rules import Rule, Check


class CheckCommentLineLen(Rule, Check):
    depends_on = ("IsComment",)

    def run(self, context):
        """
        Lines must not be over 80 characters long
        """
        i = 0
        while not context.check_token(i, ["COMMENT", "MULT_COMMENT"]):
            i += 1
        token = context.peek_token(i)
        if not token:
            return
        index = token.pos[1]
        if token.type == "MULT_COMMENT":
            lines = token.value.split("\n")
            # We need to add a padding to the first line because the comment
            # can be at the end of a line.
            lines[0] = " " * index + lines[0]
            for lineno, line in enumerate(lines, start=token.pos[0]):
                if len(line) > 81:
                    token.pos = (lineno, 1)
                    context.new_error("LINE_TOO_LONG", token)
        elif index + len(token.value) > 81:  # token.type == "COMMENT"
            context.new_error("LINE_TOO_LONG", token)

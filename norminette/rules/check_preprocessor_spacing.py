from norminette.rules import Rule, Check


class CheckPreprocessorSpacing(Rule, Check):
    depends_on = (
        "IsPreprocessorStatement",
    )

    def run(self, context):
        """
        A preprocessor line cannot end with spaces or tabs
        """
        for i in range(1, context.tkn_scope):
            if context.check_token(i, "NEWLINE") is not True:
                continue
            if context.check_token(i - 1, ["SPACE", "TAB"]) is True:
                context.new_error("SPC_BEFORE_NL", context.peek_token(i - 1))
        return False, 0

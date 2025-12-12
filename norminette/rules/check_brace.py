from norminette.rules import Rule, Check


class CheckBrace(Rule, Check):
    depends_on = (
        "IsBlockStart",
        "IsBlockEnd",
    )

    def run(self, context):
        """
        C files must end with an empty line
        Functions can only have 25 lines
        """
        i = 0
        i = context.skip_ws(i, nl=False)
        # if context.check_token(i, ["RBRACE", "LBRACE"]) is False and context.scope.type != "GlobalScope":
        #    context.new_error("BRACE_EMPTY_LINE")
        if context.check_token(i, ["RBRACE", "LBRACE"]) is False:
            context.new_error("EXPECTED_BRACE", context.peek_token(i))
            return False, 0
        i += 1
        i = context.skip_ws(i, nl=False)
        if context.check_token(i, "NEWLINE") is False or context.check_token(i, "NEWLINE") is None:
            if context.scope.name == "UserDefinedType" or context.scope.name == "UserDefinedEnum":
                i = context.skip_ws(i, nl=False)
                if context.check_token(i, "SEMI_COLON") is True:
                    return False, 0
                if context.check_token(i, "IDENTIFIER") is False:
                    context.new_error("BRACE_SHOULD_EOL", context.peek_token(i - 1))
                else:
                    i += 1
                    if context.check_token(i, "SEMI_COLON") is False:
                        context.new_error("BRACE_SHOULD_EOL", context.peek_token(i - 1))
            else:
                context.new_error("BRACE_SHOULD_EOL", context.peek_token(i - 1))
        if context.scope.name == "Function" and context.scope.lines > 26:
            context.new_error("TOO_MANY_LINES", context.peek_token(0))
        return False, 0

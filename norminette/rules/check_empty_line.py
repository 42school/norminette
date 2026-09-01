from norminette.rules import Rule, Check


class CheckEmptyLine(Rule, Check):
    def preceded_by_empty_line(self, context):
        """The norm asks for an empty line between two functions, wherever it
        falls, so a preprocessor block already separated needs no other one.
        """
        i = -2
        while context.history[i] == "IsPreprocessorStatement" and -i < len(
            context.history
        ):
            i -= 1
        return context.history[i] == "IsEmptyLine"

    def run(self, context):
        """
        Empty line must not contains tabs or spaces
        You cannot have 2 empty lines in a row
        Your variable declarations must be followed by an empty line
        No other empty lines are allowed in functions
        You must have an empty between two functions
        """
        i = 0
        if len(context.history) == 1 and context.history[-1] == "IsEmptyLine":
            context.new_error("EMPTY_LINE_FILE_START", context.peek_token(i))
            return False, 0
        if context.scope.name != "GlobalScope":
            if (
                context.history[-1] != "IsVarDeclaration"
                and context.scope.vdeclarations_allowed is True
            ):
                context.scope.vdeclarations_allowed = False
                if context.history[-1] not in ["IsEmptyLine", "IsComment"]:
                    if (
                        context.history[-1] == "IsBlockEnd"
                        and context.scope.name == "Function"
                    ):
                        pass
                    else:
                        context.new_error("NL_AFTER_VAR_DECL", context.peek_token(i))
                        return True, i
        if (
            len(context.history) > 1
            and context.history[-2] == "IsPreprocessorStatement"
            and context.history[-1] != "IsPreprocessorStatement"
            and context.history[-1] != "IsEmptyLine"
            and context.history[-1] != "IsComment"
            and self.preceded_by_empty_line(context) is False
        ):
            context.new_error("NL_AFTER_PREPROC", context.peek_token(i))
        if context.history[-1] != "IsEmptyLine":
            return False, 0
        if context.check_token(i, "NEWLINE") is False:
            context.new_error("SPACE_EMPTY_LINE", context.peek_token(i))
        if context.history[-2] == "IsEmptyLine":
            context.new_error("CONSECUTIVE_NEWLINES", context.peek_token(i))
        if (
            context.history[-2] != "IsVarDeclaration"
            and context.scope.name != "GlobalScope"
        ):
            context.new_error("EMPTY_LINE_FUNCTION", context.peek_token(0))
        if context.check_token(i, "NEWLINE") and context.peek_token(i + 1) is None:
            context.new_error("EMPTY_LINE_EOF", context.peek_token(i))

        return False, 0

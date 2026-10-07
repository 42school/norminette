from norminette.rules import Rule, Check


class CheckComment(Rule, Check):
    def run(self, context):
        """
        Comments are forbidden inside functions and in the middle of instructions.
        """
        i = context.skip_ws(0)

        # Only the statement that just matched, otherwise every comment on the
        # line is reported once per rule that runs on it
        tokens = []
        while i < context.tkn_scope and context.peek_token(i):
            token = context.peek_token(i)
            tokens.append(token)
            i += 1

        for index, token in enumerate(tokens):
            if token.type in ("COMMENT", "MULT_COMMENT"):
                if self.is_inside_a_function(context):
                    context.new_error("WRONG_SCOPE_COMMENT", token)
                if index == 0 or self.is_last_token(token, tokens[index+1:]):
                    continue
                context.new_error("COMMENT_ON_INSTR", token)

    def is_inside_a_function(self, context):
        if context.history[-2:] == ["IsFuncDeclaration", "IsBlockStart"]:
            return True
        if context.scope.__class__.__name__.lower() == "function":
            return True
        # Sometimes the context scope is a `ControlStructure` scope instead of
        # `Function` scope, so, to outsmart this bug, we follow the braces of
        # the last function body in `context.history` ourselves. Only the
        # records added since the last call are read, otherwise every comment
        # rescans the whole history.
        history = context.history
        for index in range(context.history_read, len(history)):
            record = history[index]
            if record == "IsBlockStart" and index and history[index - 1] == "IsFuncDeclaration":
                context.function_depth = 1
            elif context.function_depth and record == "IsBlockStart":
                context.function_depth += 1
            elif context.function_depth and record == "IsBlockEnd":
                context.function_depth -= 1
        context.history_read = len(history)
        return context.function_depth > 0

    def is_last_token(self, token, foward):
        # A comment ends its own line, so an instruction continuing on the
        # next one does not put it in the middle of anything
        for it in foward:
            if it.type == "NEWLINE":
                return True
            if it.type not in ("SPACE", "TAB", "COMMENT", "MULT_COMMENT"):
                return False
        return True

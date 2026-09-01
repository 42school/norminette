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
        # `Function` scope, so, to outsmart this bug, we need check manually
        # the `context.history`.
        last = None
        for index, record in enumerate(reversed(context.history)):
            if record == "IsFuncDeclaration" and last == "IsBlockStart":
                # Since the limited history API, we can't say if we're in a
                # nested function to reach the first enclosing function, so,
                # we'll consider that the user just declared a normal function
                # in global scope.
                stack = 1
                index -= 1  # Jumps to next record after `IsBlockStart`
                while index > 0 and stack > 0:
                    record = context.history[-index]
                    index -= 1
                    if record not in ("IsBlockStart", "IsBlockEnd"):
                        continue
                    stack = stack + (1, -1)[record == "IsBlockEnd"]
                return bool(stack)
            last = record
        return False

    def is_last_token(self, token, foward):
        # A comment ends its own line, so an instruction continuing on the
        # next one does not put it in the middle of anything
        for it in foward:
            if it.type == "NEWLINE":
                return True
            if it.type not in ("SPACE", "TAB", "COMMENT", "MULT_COMMENT"):
                return False
        return True

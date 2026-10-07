from norminette.rules import Rule, Check


class CheckGeneralSpacing(Rule, Check):
    depends_on = (
        "IsDeclaration",
        "IsControlStatement",
        "IsExpressionStatement",
        "IsAssignation",
        "IsFunctionCall",
    )

    def is_indent(self, context, pos):
        """Returns True if the tab at 'pos' belongs to the run opening its line"""
        line = context.peek_token(pos).pos[0]
        while pos > 0 and context.check_token(pos - 1, "TAB") is True:
            if context.peek_token(pos - 1).pos[0] != line:
                return False
            pos -= 1
        return context.peek_token(pos).pos[1] == 1

    def run(self, context):
        """
        Checks for tab/space consistency
        """
        if context.scope.name == "UserDefinedType":
            return False, 0
        i = context.skip_ws(0)
        while i < context.tkn_scope:
            # Leading tabs open a line, the indentation rules own them
            if context.check_token(i, "TAB") is True and not self.is_indent(context, i):
                context.new_error("TAB_INSTEAD_SPC", context.peek_token(i))
                break
            if context.check_token(i, ["NEWLINE", "ESCAPED_NEWLINE"]) is True:
                i = context.skip_ws(i + 1, nl=True)
            i += 1
        return False, 0

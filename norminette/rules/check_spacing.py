from norminette.rules import Rule, Check


class CheckSpacing(Rule, Check):
    def run(self, context):
        """
        Indentation (except for preprocessors) must be done with tabs
        There cannot be trailing spaces or tabs at the end of line
        """
        i = 0
        if context.history[-1] in ("IsEmptyLine", "IsPreprocessorStatement"):
            return False, 0
        space_tab_error = False
        space_error = False
        while i in range(len(context.tokens[: context.tkn_scope])):
            if context.check_token(i, "SPACE"):
                if context.check_token(i - 1 if i > 0 else 0, "TAB"):
                    if space_tab_error is False:
                        context.new_error("MIXED_SPACE_TAB", context.peek_token(i - 1))
                        space_tab_error = True
                if context.peek_token(i).pos[1] == 1:
                    while i < context.tkn_scope and context.check_token(i, "SPACE"):
                        i += 1
                    if context.check_token(i + 1, "NEWLINE"):
                        i += 1
                        continue
                    context.new_error("SPACE_REPLACE_TAB", context.peek_token(i))
                    continue
                i += 1
                if context.check_token(i, "SPACE"):
                    if space_error is False:
                        context.new_error("CONSECUTIVE_SPC", context.peek_token(i - 1))
                        space_error = True
                    while i < context.tkn_scope and context.check_token(i, "SPACE"):
                        i += 1
                if context.check_token(i, "TAB"):
                    if space_tab_error is False:
                        context.new_error("MIXED_SPACE_TAB", context.peek_token(i - 1))
                        space_tab_error = True
            elif context.check_token(i, "TAB"):
                if context.peek_token(i).pos[1] == 1:
                    while context.check_token(i, "TAB"):
                        i += 1
                    if context.check_token(i, "NEWLINE"):
                        context.new_error("SPC_BEFORE_NL", context.peek_token(i - 1))
                else:
                    i += 1
            else:
                i += 1
        return False, 0

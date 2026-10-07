from norminette.rules import Rule, Check

type_specifiers = ["CHAR", "DOUBLE", "ENUM", "FLOAT", "INT", "UNION", "VOID", "SHORT"]

misc_specifiers = ["CONST", "REGISTER", "STATIC", "STRUCT", "VOLATILE"]

size_specifiers = ["LONG", "SHORT"]

sign_specifiers = ["SIGNED", "UNSIGNED"]

whitespaces = ["SPACE", "TAB", "NEWLINE"]

arg_separator = ["COMMA", "CLOSING_PARENTHESIS"]


class CheckFuncArgumentsName(Rule, Check):
    depends_on = (
        "IsFuncDeclaration",
        "IsFuncPrototype",
    )

    def check_arg_format(self, context, pos):
        """
        A valid argument contains either:
        - a type specifier AND a paramater name (IDENTIFIER)
        - an ellipsis
        """

        i = context.skip_ws(pos)
        p = 0
        stop = ["COMMA", "RPARENTHESIS"]
        if context.check_token(i, ["COMMENT", "MULT_COMMENT"]):
            # context.new_error("WRONG_SCOPE_COMMENT", context.peek_token(i))
            i += 1
        # if context.check_token(i, "NEWLINE"):
        # context.new_error("NEWLINE_IN_DECL", context.peek_token(i))
        # i += 1
        if context.check_token(i, "ELLIPSIS"):
            i += 1
            if context.peek_token(i).type in stop:
                i += 1
            return i
        ret, i = context.check_type_specifier(i)
        has_tab = False
        while context.check_token(i, ["SPACE", "TAB"]):
            if context.check_token(i, "TAB") is True and has_tab is False:
                context.new_error("TAB_INSTEAD_SPC", context.peek_token(i))
                has_tab = True
            i += 1

        if ret is False:
            context.new_error("ARG_TYPE_UKN", context.peek_token(i))
            return -1
        while context.peek_token(i) is not None and context.check_token(
            i, ["LPARENTHESIS"] + whitespaces
        ):
            if context.check_token(i, "LPARENTHESIS") is True:
                p += 1
            if context.check_token(i, "RPARENTHESIS") is True:
                p -= 1
            i += 1

        if ret is True:
            i = context.skip_misc_specifier(i)
            ret, i = context.check_identifier(i)
            if ret is False:
                context.new_error("MISSING_IDENTIFIER", context.peek_token(i - 1))
            else:
                i += 1
                i = context.skip_ws(i)
            while context.peek_token(i) is not None and i < context.arg_pos[1]:
                if context.check_token(i, stop) is True:
                    if context.check_token(i, "RPARENTHESIS") is True and p > 0:
                        p -= 1
                    else:
                        break
                if context.check_token(i, "LPARENTHESIS"):
                    i = context.skip_nest(i)
                i += 1
            i += 1

        else:
            while (
                context.peek_token(i) is not None
                and context.peek_token(i).type not in stop
            ):
                i += 1
            i += 1
        return i

    def no_arg_func(self, context, pos):
        i = context.skip_ws(pos, nl=True)
        if context.check_token(i, "VOID"):
            i += 1
            i = context.skip_ws(i, nl=True)
            if context.check_token(i, "RPARENTHESIS"):
                return True
        elif context.check_token(i, "RPARENTHESIS"):
            return True
        return False

    def empty_arg_lists(self, context):
        """Every `()` in a function header is an argument list, the
        function's own or that of a function pointer it takes or returns.
        """
        for i in range(0, context.tkn_scope):
            if context.check_token(i, "LPARENTHESIS") is not True:
                continue
            tmp = context.skip_ws(i + 1, nl=True)
            if context.check_token(tmp, "RPARENTHESIS") is True:
                context.new_error("NO_ARGS_VOID", context.peek_token(tmp))

    def run(self, context):
        """
        Empty functions arguments must use void
        """
        self.empty_arg_lists(context)
        i = context.arg_pos[0] + 1
        if self.no_arg_func(context, i) is True:
            return False, 0
        while i < context.arg_pos[1]:
            i = context.skip_ws(i)
            if context.check_token(i, "NEWLINE"):
                i += 1
                continue
            if context.check_token(i, "LPARENTHESIS"):
                p = 1
                while p:
                    if context.peek_token(i) is not None:
                        if context.check_token(i, "LPARENTHESIS"):
                            p += 1
                        elif context.check_token(i, "RPARENTHESIS"):
                            p -= 1
                    else:
                        break
                    i += 1
            elif context.check_token(i, "LBRACKET") is True:
                i = context.skip_nest(i) + 1
            elif context.check_token(i, "COMMA") is True:
                i += 1
            elif context.check_token(i, "RPARENTHESIS") is not True:
                i = self.check_arg_format(context, i)
                if i == -1:
                    return False, 0
        return False, 0

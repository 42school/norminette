from norminette.rules import Rule, Check

whitespaces = ["SPACE", "TAB", "NEWLINE"]

type_specifiers = ["CHAR", "DOUBLE", "ENUM", "FLOAT", "INT", "UNION", "VOID", "SHORT"]

misc_specifiers = ["CONST", "REGISTER", "STATIC", "STRUCT", "VOLATILE"]

size_specifiers = ["LONG", "SHORT"]

sign_specifiers = ["SIGNED", "UNSIGNED"]

arg_separator = ["COMMA", "CLOSING_PARENTHESIS"]


class CheckFuncSpacing(Rule, Check):
    depends_on = (
        "IsFuncDeclaration",
    )

    def run(self, context):
        """
        Function return type and function name must be separated by a tab
        """
        i = 0
        while i < context.fname_pos:
            if context.check_token(i, "IDENTIFIER") is True and context.peek_token(i).value == "__attribute__":
                # context.new_error("ATTR_EOL", context.peek_token(i))
                break
            i += 1
        i = context.fname_pos - 1
        while context.check_token(i, ["MULT", "BWISE_AND", "LPARENTHESIS"]) is True:
            i -= 1
        if context.peek_token(i) is None:
            # Nothing before the name: the missing type is reported elsewhere
            return False, 0
        if context.peek_token(i).type == "SPACE":
            context.new_error("SPACE_BEFORE_FUNC", context.peek_token(i))
            return False, 0
        if context.peek_token(i).type == "TAB":
            j = i
            while context.peek_token(j).type == "TAB":
                j -= 1
            if j + 1 < i:
                context.new_error("TOO_MANY_TABS_FUNC", context.peek_token(i))
            if context.peek_token(i).type == "SPACE":
                context.new_error("SPACE_BEFORE_FUNC", context.peek_token(i))
        else:
            context.new_error("MISSING_TAB_FUNC", context.peek_token(i))
        return False, 0

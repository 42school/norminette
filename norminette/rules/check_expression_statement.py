from norminette.rules import Rule, Check

kw = [
    # C reserved keywords #
    "AUTO",
    "BREAK",
    "CASE",
    "CHAR",
    "CONST",
    "CONTINUE",
    "DEFAULT",
    "DO",
    "DOUBLE",
    "ELSE",
    "ENUM",
    "EXTERN",
    "FLOAT",
    "FOR",
    "GOTO",
    "IF",
    "INT",
    "LONG",
    "REGISTER",
    "RETURN",
    "SHORT",
    "SIGNED",
    "STATIC",
    "STRUCT",
    "SWITCH",
    "TYPEDEF",
    "UNION",
    "UNSIGNED",
    "VOID",
    "VOLATILE",
    "WHILE",
]


class CheckExpressionStatement(Rule, Check):
    depends_on = (
        "IsExpressionStatement",
        "IsControlStatement",
        "IsFunctionCall",
        "IsAssignation",
        "IsCast",
    )

    def check_comma_operator(self, context, start, end):
        """A comma between the parentheses of a return separates instructions,
        the norm allows only one per line. A comma nested deeper belongs to a
        call and is left alone.
        """
        depth = 0
        for i in range(start, end):
            if context.check_token(i, ["LPARENTHESIS", "LBRACKET", "LBRACE"]):
                depth += 1
            elif context.check_token(i, ["RPARENTHESIS", "RBRACKET", "RBRACE"]):
                depth -= 1
            elif depth == 1 and context.check_token(i, "COMMA"):
                context.new_error("TOO_MANY_INSTR", context.peek_token(i))
                return

    def run(self, context):
        """
        C keywords (return, break, continue...) must be followed by a space, with the
        exception of sizeof
        Return values in a function must be contained in parenthesis
        """
        i = 0
        while context.check_token(i, ["SEMI_COLON", "NEWLINE"]) is False:
            if context.check_token(i, kw) is True:
                if (
                    context.check_token(
                        i + 1,
                        ["SPACE", "NEWLINE", "RPARENTHESIS", "COMMENT", "MULT_COMMENT"],
                    )
                    is False
                ):
                    context.new_error("SPACE_AFTER_KW", context.peek_token(i))
            if context.check_token(i, ["MULT", "BWISE_AND"]) is True and i > 0:
                if context.check_token(i - 1, "IDENTIFIER") is True:
                    context.new_error("SPACE_AFTER_KW", context.peek_token(i - 1))
            if context.check_token(i, "RETURN") is True:
                tmp = i + 1
                tmp = context.skip_ws(tmp)
                if (
                    context.check_token(tmp, "SEMI_COLON") is False
                    and context.check_token(tmp, "LPARENTHESIS") is False
                ):
                    context.new_error("RETURN_PARENTHESIS", context.peek_token(tmp))
                    return False, 0
                elif context.check_token(tmp, "SEMI_COLON") is False:
                    end = context.skip_nest(tmp)
                    self.check_comma_operator(context, tmp, end)
                    tmp = end + 1
                    if context.check_token(tmp, "SEMI_COLON") is False:
                        context.new_error("RETURN_PARENTHESIS", context.peek_token(tmp))
                        return False, 0
            i += 1
        return False, 0

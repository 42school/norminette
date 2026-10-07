from norminette.rules import Rule, Check

types = [
    "CHAR",
    "DOUBLE",
    "ENUM",
    "FLOAT",
    "INT",
    "LONG",
    "SHORT",
    "SIGNED",
    "STRUCT",
    "UNION",
    "UNSIGNED",
    "VOID",
    "IDENTIFIER",
]


class CheckReturnType(Rule, Check):
    depends_on = (
        "IsFuncDeclaration",
        "IsFuncPrototype",
    )

    def run(self, context):
        """
        A function must declare its return type
        """
        for i in range(0, context.fname_pos):
            if context.check_token(i, types) is True:
                return False, 0
        context.new_error("MISSING_RETURN_TYPE", context.peek_token(context.fname_pos))
        return False, 0

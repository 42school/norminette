from norminette.rules import Rule, Check


types = [
    "INT",
    "VOID",
    "CHAR",
    "LONG",
    "DOUBLE",
    "SHORT",
    "SIGNED",
    "UNSIGNED",
    "STATIC",
    "CONST",
    "IDENTIFIER",
    "ENUM",
    "STRUCT",
    "UNION",
    "VOLATILE",
    "EXTERN",
    "SPACE",
    "TAB",
]


class CheckGlobalNaming(Rule, Check):
    depends_on = (
        "IsVarDeclaration",
    )

    def run(self, context):
        """
        Global variable names must be preceded by g_
        """
        i = 0
        if context.scope.name != "GlobalScope":
            return False, 0
        i = context.skip_ws(i)
        _, i = context.check_type_specifier(i)
        i = context.skip_ws(i)
        while context.check_token(i, "IDENTIFIER") is False:
            i += 1
        if (
            context.peek_token(i) is not None
            and context.peek_token(i).value != "environ"
        ):
            if context.allow_globals is False:
                context.new_error("GLOBAL_VAR_DETECTED", context.peek_token(0))
            if context.peek_token(i).value.startswith("g_") is False:
                context.new_error("GLOBAL_VAR_NAMING", context.peek_token(i))
        return False, i

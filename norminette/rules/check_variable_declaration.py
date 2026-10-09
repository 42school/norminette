from norminette.rules import Rule, Check

assigns = [
    "RIGHT_ASSIGN",
    "LEFT_ASSIGN",
    "ADD_ASSIGN",
    "SUB_ASSIGN",
    "MUL_ASSIGN",
    "DIV_ASSIGN",
    "MOD_ASSIGN",
    "AND_ASSIGN",
    "XOR_ASSIGN",
    "OR_ASSIGN",
    "ASSIGN",
]


class CheckVariableDeclaration(Rule, Check):
    depends_on = (
        "IsVarDeclaration",
    )

    def run(self, context):
        """
        Variables can be declared as global or in the scope of a function
        Only static variables, global variables, and constants can be initialised at declaration.
        Each variable must be declared on a separate line
        """
        i = 0
        static_or_const = False
        passed_assign = False
        if context.scope.name == "Function":
            context.scope.vars += 1
            if context.scope.vars > 5:
                context.new_error("TOO_MANY_VARS_FUNC", context.peek_token(i))
            if (
                context.history[-2] != "IsBlockStart"
                and context.history[-2] != "IsVarDeclaration"
            ):
                context.new_error("VAR_DECL_START_FUNC", context.peek_token(i))
            elif context.scope.vdeclarations_allowed is False:
                context.new_error("VAR_DECL_START_FUNC", context.peek_token(i))
            elif context.scope.vdeclarations_allowed is None:
                context.scope.vdeclarations_allowed = True
        elif (
            context.scope.name == "GlobalScope"
            or context.scope.name == "UserDefinedType"
        ):
            pass
        else:
            context.new_error("WRONG_SCOPE_VAR", context.peek_token(i))
        tmp = 0
        ret, tmp = context.check_type_specifier(tmp)
        tmp = context.skip_ws(tmp)
        tmp -= 1
        identifier = False
        while context.check_token(tmp, ["SEMI_COLON"] + assigns) is False:
            if context.check_token(tmp, "IDENTIFIER"):
                identifier = True
            tmp += 1
        if identifier is False:
            context.new_error("IMPLICIT_VAR_TYPE", context.peek_token(0))
            return False
        # `void *(*const f)(size_t) = malloc;` qualifies the declarator
        tmp = 0
        while context.peek_token(tmp) and context.check_token(
            tmp, ["SEMI_COLON"] + assigns
        ) is False:
            if (
                context.check_token(tmp, "LPARENTHESIS") is True
                and context.parenthesis_contain(tmp)[0] != "pointer"
            ):
                tmp = context.skip_nest(tmp)
            elif context.check_token(tmp, ["STATIC", "CONST"]) is True:
                static_or_const = True
            tmp += 1
        while context.peek_token(i) and context.check_token(i, "SEMI_COLON") is False:
            if context.check_token(i, "LPARENTHESIS") is True:
                i = context.skip_nest(i)
            if context.check_token(i, "ASSIGN") is True:
                passed_assign = True
            if context.check_token(i, ["STATIC", "CONST"]) is True:
                static_or_const = True
            if context.check_token(i, assigns) is True and static_or_const is False:
                if context.scope.name == "GlobalScope":
                    i += 1
                    continue
                context.new_error("DECL_ASSIGN_LINE", context.peek_token(i))
            if context.check_token(i, "COMMA") is True and passed_assign is False:
                context.new_error("MULT_DECL_LINE", context.peek_token(i))
            i += 1
        return False, 0

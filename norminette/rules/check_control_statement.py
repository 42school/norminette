from norminette.rules import Rule, Check


forbidden_cs = ["FOR", "SWITCH", "CASE", "GOTO"]
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


class CheckControlStatement(Rule, Check):
    depends_on = (
        "IsControlStatement",
    )

    def check_nest(self, context, i):
        depth = 1
        braces = 0
        i += 1
        while depth > 0 and context.peek_token(i) is not None:
            if context.check_token(i, "LPARENTHESIS") is True:
                depth += 1
            if context.check_token(i, "RPARENTHESIS") is True:
                depth -= 1
            if context.check_token(i, "LBRACE") is True:
                braces += 1
            if context.check_token(i, "RBRACE") is True:
                braces -= 1
            # `(t_x){.i = v}`: a designated initialiser is not an assignment
            if context.check_token(i, assigns) is True and braces == 0:
                context.new_error("ASSIGN_IN_CONTROL", context.peek_token(i))
                return -1
            if context.check_token(i, forbidden_cs) is True:
                context.new_error("FORBIDDEN_CS", context.peek_token(i))
            if context.check_token(i, "NEWLINE") is True and depth < 1:
                return
            i += 1
        return

    def run(self, context):
        """
        Forbidden control structures:
            - For
            - Switch case
            - Goto
        Assignations must be done outside of control structures
        """
        i = 0
        if context.scope.name == "GlobalScope":
            context.new_error("WRONG_SCOPE", context.peek_token(0))
        while context.check_token(i, "NEWLINE") is False:
            if context.check_token(i, "SEMI_COLON") is True:
                context.new_error("EXP_NEWLINE", context.peek_token(i))
                return True, i
            if context.check_token(i, forbidden_cs) is True:
                context.new_error("FORBIDDEN_CS", context.peek_token(i))
                return True, i
            elif context.check_token(i, "LPARENTHESIS") is True:
                if self.check_nest(context, i) == -1:
                    return True, i
            i += 1
        if i < context.tkn_scope:
            i += 1
            indent = 0
            while context.check_token(i, ["TAB"]) is True:
                i += 1
                indent += 1
            if context.check_token(i, "SEMI_COLON") is True:
                if indent > context.scope.indent + 1:
                    context.new_error("TOO_MANY_TAB", context.peek_token(i))
                if indent < context.scope.indent + 1:
                    context.new_error("TOO_FEW_TAB", context.peek_token(i))
        return False, 0

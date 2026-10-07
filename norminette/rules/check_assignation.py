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

special_assigns = ["INC", "DEC"]


class CheckAssignation(Rule, Check):
    depends_on = (
        "IsAssignation",
    )

    def check_brace_assign(self, context, i):
        i += 1
        deep = 1
        while context.check_token(i, "RBRACE") is False and deep > 0:
            i += 1
        return True, i

    def nested_assign(self, context, start, end):
        """Parentheses do not turn a second assignment into one"""
        for i in range(start + 1, end):
            if context.check_token(i, assigns) is True:
                context.new_error("MULT_ASSIGN_LINE", context.peek_token(i))
                return

    def check_assign_right(self, context, i, mini_assign=False):
        tmp_typ = None
        start = 0
        while context.check_token(i, "SEMI_COLON") is False:
            typ = None
            if context.check_token(i, "LBRACE"):
                ret, i = self.check_brace_assign(context, i)
                if ret is False:
                    return True, i
                break
            if context.check_token(i, "LPARENTHESIS") is True:
                start = i
                tmp_typ, i = context.parenthesis_contain(i)
                if tmp_typ is not None:
                    typ = tmp_typ
                if tmp_typ == "assign":
                    context.new_error("MULT_ASSIGN_LINE", context.peek_token(start))
                else:
                    self.nested_assign(context, start, i)
                if tmp_typ is None:
                    tmp = start + 1
                    while (
                        context.peek_token(tmp)
                        and context.check_token(tmp, "RPARENTHESIS") is False
                    ):
                        if (
                            context.check_token(tmp, "COMMA") is True
                            and typ is not None
                        ):
                            context.new_error("TOO_MANY_INSTR", context.peek_token(tmp))
                        tmp += 1
            if context.check_token(i, assigns) is True:
                if mini_assign is True:
                    mini_assign = False
                else:
                    context.new_error("MULT_ASSIGN_LINE", context.peek_token(i))
            if context.check_token(i, special_assigns) is True:
                if mini_assign is True:
                    context.new_error("MULT_ASSIGN_LINE", context.peek_token(i))
            i += 1
        return False, 0

    def run(self, context):
        """
        Only one assignation at a time
        Unless the variable is static (or global), you cannot assign its value when you declare it.
        """
        i = 0
        assign_present = False
        mini_assign = False
        while context.check_token(i, "SEMI_COLON") is False:
            if (
                context.check_token(i, assigns + special_assigns) is True
                and assign_present is False
            ):
                assign_present = True
                if context.check_token(i, special_assigns):
                    mini_assign = True
                return self.check_assign_right(context, i + 1, mini_assign)
            i += 1
        return False, 0

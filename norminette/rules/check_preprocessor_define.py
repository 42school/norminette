from norminette.rules import Rule, Check

values = ["CONSTANT", "IDENTIFIER", "STRING", "CHAR_CONST", "NULL"]

unary = ["MINUS", "PLUS", "NOT", "BWISE_NOT"]

binary = [
    "MULT", "DIV", "MODULO",
    "LESS_THAN", "MORE_THAN", "LESS_OR_EQUAL", "GREATER_OR_EQUAL",
    "EQUALS", "NOT_EQUAL", "AND", "OR",
    "BWISE_AND", "BWISE_OR", "BWISE_XOR",
    "RIGHT_SHIFT", "LEFT_SHIFT",
]


class CheckPreprocessorDefine(Rule, Check):
    depends_on = (
        "IsPreprocessorStatement",
    )

    def run(self, context):
        """
        Defined names must be in capital letters
        Define can only contain constant values, such as integers and strings
        """
        i = context.skip_ws(0)
        i += 1  # skip HASH
        i = context.skip_ws(i)
        if not context.check_token(i, "IDENTIFIER"):
            return
        if not context.peek_token(i).value == "define":
            return
        if context.preproc.skip_define:
            return
        i += 1  # skip DEFINE
        i = context.skip_ws(i)

        if not context.peek_token(i).value.isupper():
            context.new_error("MACRO_NAME_CAPITAL", context.peek_token(i))
        i += 1  # skip macro name

        if context.check_token(i, "LPARENTHESIS"):
            context.new_error("MACRO_FUNC_FORBIDDEN", context.peek_token(i))
            while not context.check_token(i, "RPARENTHESIS"):
                i += 1
            i += 1
        i = context.skip_ws(i)

        # A define holds a literal or a constant expression: operands and
        # operators alternating, with balanced parentheses
        depth = 0
        wants_operand = True
        empty = True
        last = i
        while context.peek_token(i) and not context.check_token(i, "NEWLINE"):
            if context.check_token(i, ["SPACE", "TAB", "COMMENT", "MULT_COMMENT"]):
                i += 1
                continue
            last = i
            empty = False
            if context.check_token(i, "LPARENTHESIS"):
                if wants_operand is False:
                    return context.new_error("PREPROC_CONSTANT", context.peek_token(i))
                depth += 1
            elif context.check_token(i, "RPARENTHESIS"):
                depth -= 1
                if depth < 0 or wants_operand is True:
                    return context.new_error("PREPROC_CONSTANT", context.peek_token(i))
            elif context.check_token(i, values):
                if wants_operand is False:
                    return context.new_error("PREPROC_CONSTANT", context.peek_token(i))
                wants_operand = False
            elif context.check_token(i, unary):
                wants_operand = True
            elif context.check_token(i, binary):
                if wants_operand is True:
                    return context.new_error("PREPROC_CONSTANT", context.peek_token(i))
                wants_operand = True
            else:
                return context.new_error("PREPROC_CONSTANT", context.peek_token(i))
            i += 1
        # A header guard defines a name with no value at all
        if empty is False and (depth != 0 or wants_operand is True):
            context.new_error("PREPROC_CONSTANT", context.peek_token(last))

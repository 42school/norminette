from norminette.rules import Rule, Check
from norminette.errors import Error

types = ["INT", "FLOAT", "CHAR", "DOUBLE", "LONG", "SHORT"]


class CheckFuncDeclaration(Rule, Check):
    depends_on = (
        "IsFuncDeclaration",
        "IsFuncPrototype",
        "IsUserDefinedType",
    )

    def run(self, context):
        """
        Maximum 4 arguments in a function
        Function declaration must be preceded by a newline
        """
        # pdb.set_trace()
        i = 0
        tmp = 0
        start = 0
        arg = 1
        while context.check_token(tmp, ["SEMI_COLON", "NEWLINE"]) is False:
            if context.check_token(tmp, "LBRACE") is True:
                token = context.peek_token(tmp)
                error = Error.from_name("BRACE_NEWLINE")
                error.add_highlight(*token.pos, length=1)
                context.errors.add(error)
            tmp += 1
        if context.history[-1] == "IsUserDefinedType":
            return
        # if tmp < context.tkn_scope - 2:
        # context.new_error("NEWLINE_IN_DECL", context.peek_token(tmp))
        # this is a func declaration
        if context.history[-1] == "IsFuncDeclaration":
            #        if context.check_token(tmp, "SEMI_COLON") is False:
            i = 2
            length = len(context.history)
            while length - i >= 0 and (
                context.history[-i] == "IsPreprocessorStatement"
                or context.history[-i] == "IsComment"
                or context.history[-i] == "IsFuncDeclaration"
            ):
                i += 1
            if length - i > 0 and context.history[-i] != "IsEmptyLine":
                context.new_error("NEWLINE_PRECEDES_FUNC", context.peek_token(start))
        i = context.fname_pos + 1
        while (
            context.check_token(i, ["RPARENTHESIS"])
        ) is True:  # , "SPACE", "TAB"])) is True:
            i += 1
        if context.check_token(i, "LPARENTHESIS") is False:
            context.new_error("EXP_PARENTHESIS", context.peek_token(i))
        i = context.skip_ws(i)
        i += 1
        deep = 1
        while deep > 0 and context.peek_token(i) is not None:
            if context.check_token(i, "LPARENTHESIS"):
                i = context.skip_nest(i)
            elif context.check_token(i, "RPARENTHESIS"):
                deep -= 1
            elif context.check_token(i, "COMMA"):
                arg += 1
            i += 1
        if context.check_token(i - 1, ["SPACE", "TAB"]) is True:
            tmp = i - 1
            while context.check_token(tmp, ["SPACE", "TAB"]) is True:
                tmp -= 1
            if context.check_token(tmp, "NEWLINE") is False:
                context.new_error("NO_SPC_BFR_PAR", context.peek_token(i))
        if arg > 4:
            context.new_error("TOO_MANY_ARGS", context.peek_token(i))
        arg = []
        while context.check_token(i, ["NEWLINE", "SEMI_COLON"]) is False:
            i += 1
        return False, 0

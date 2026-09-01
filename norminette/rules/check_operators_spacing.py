from norminette.rules import Rule, Check

operators = [
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
    "LESS_OR_EQUAL",
    "GREATER_OR_EQUAL",
    "EQUALS",
    "NOT_EQUAL",
    "ASSIGN",
    # "COLON",
    # "SEMI_COLON",
    # "COMMA",
    # "DOT",
    "NOT",
    "MINUS",
    "PLUS",
    "MULT",
    "DIV",
    "MODULO",
    "LESS_THAN",
    "MORE_THAN",
    "ELLIPSIS",
    "INC",
    "DEC",
    "PTR",
    "AND",
    "OR",
    "BWISE_XOR",
    "BWISE_OR",
    "BWISE_NOT",
    "BWISE_AND",
    "RIGHT_SHIFT",
    "LEFT_SHIFT",
    "TERN_CONDITION",
]

assign_operators = [
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

gps_operators = []

ps_operators = [
    # operators that should be prefixed and suffixed by a space
    "RIGHT_ASSIGN",  # >>=
    "LEFT_ASSIGN",  # <<=
    "ADD_ASSIGN",  # +=
    "SUB_ASSIGN",  # -=
    "MUL_ASSIGN",  # *=
    "DIV_ASSIGN",  # /=
    "MOD_ASSIGN",  # %=
    "AND_ASSIGN",  # &=
    "XOR_ASSIGN",  # ^=
    "OR_ASSIGN",  # |=
    "LESS_OR_EQUAL",  # <=
    "GREATER_OR_EQUAL",  # >=
    "EQUALS",  # ==
    "NOT_EQUAL",  # !=
    "ASSIGN",  # =
    "DIV",  # /
    "MULT",  # *
    "MODULO",  # %
    "LESS_THAN",  # <
    "MORE_THAN",  # >
    "AND",  # &
    "OR",  # |
    "RIGHT_SHIFT",  # >>
    "LEFT_SHIFT",  # <<
    "TERN_CONDITION",  # ?
]

p_operators = [
    # operators that should only be prefixed by a space
    "ELLIPSIS"  # ...
]

s_operators = [
    # operators that should only be suffixed by a space
    "COMMA",  # ,
    # Where do i put that shit
    # "COLON",  # :
]

son_operators = [
    # operators that should only be suffixed by a space or newline
    "SEMI_COLON"  # ;
]

c_operators = [
    # operators that could be "glued" with another token ("x + *y", "5 + -5")
    "PLUS",
    "MINUS",
    "BWISE_XOR",  # ^
    "BWISE_OR",  # |
    "BWISE_AND",  # &
    "BWISE_NOT",  # ~
]

glued_operators = ["MULT", "PLUS", "MINUS", "DIV", "NOT", "BWISE_NOT"]

spec_operators = [
    "NOT",
    "BWISE_NOT",
    "DIV",
]

rnests = ["RPARENTHESIS", "RBRACE", "RBRACKET"]

lnests = [
    "LBRACE",
    "LBRACKET",
    "LPARENTHESIS",
]

left_auth = []

right_auth = []

whitespaces = ["NEWLINE", "SPACE", "TAB"]


class CheckOperatorsSpacing(Rule, Check):
    depends_on = (
        "IsFuncDeclaration",
        "IsFuncPrototype",
        "IsExpressionStatement",
        "IsAssignation",
        "IsControlStatement",
        "IsVarDeclaration",
        "IsFunctionCall",
        "IsDeclaration",
    )

    def check_prefix(self, context, pos):
        if pos > 0 and context.check_token(pos, ["TAB", "SPACE"]):
            context.new_error("", context.peek_token(pos))
        if (
            pos + 1 < len(context.tokens[: context.tkn_scope])
            and context.peek_token(pos + 1).type == "SPACE"
        ):
            context.new_error("NO_SPC_AFR_OPR", context.peek_token(pos))

    def check_lnest(self, context, pos):
        if (
            context.history[-1] == "IsFuncDeclaration"
            or context.history[-1] == "IsFuncPrototype"
        ):
            return False
        tmp = pos + 1
        # Here is `(_`
        while (
            context.peek_token(tmp)
            and context.check_token(tmp, ["SPACE", "TAB"]) is True
        ):
            tmp += 1
        if context.check_token(tmp, "NEWLINE") is False:
            if (
                context.check_token(tmp, lnests + rnests + ["SEMI_COLON", "PTR", "DOT"])
                is True
                and tmp != pos + 1
            ):
                context.new_error("SPC_AFTER_PAR", context.peek_token(pos))
            elif (
                context.check_token(tmp, lnests + rnests + ["SEMI_COLON", "PTR", "DOT"])
                is False
                and tmp != pos + 1
            ):
                context.new_error("NO_SPC_AFR_PAR", context.peek_token(pos))
        tmp = pos - 1
        # Here is `_(`
        while tmp >= 0 and context.check_token(tmp, ["SPACE", "TAB"]) is True:
            tmp -= 1
        if context.check_token(tmp, "NEWLINE") is False:
            if (
                context.check_token(
                    tmp,
                    lnests
                    + rnests
                    + [
                        "SEMI_COLON",
                        "PTR",
                        "DOT",
                        "INC",
                        "DEC",
                        "MULT",
                        "BWISE_AND",
                        "IDENTIFIER",
                        "SIZEOF",
                    ],
                )
                is True
                and tmp != pos - 1
            ):
                if (
                    context.check_token(tmp, ["MULT", "BWISE_AND"]) is True
                    and context.is_operator is False
                ):
                    context.new_error("NO_SPC_BFR_PAR", context.peek_token(pos))
            elif (
                context.check_token(
                    tmp,
                    lnests
                    + rnests
                    + [
                        "SEMI_COLON",
                        "PTR",
                        "DOT",
                        "INC",
                        "DEC",
                        "MULT",
                        "BWISE_AND",
                        "BWISE_OR",
                        "BWISE_XOR",
                        "BWISE_NOT",
                        "IDENTIFIER",
                        "SIZEOF",
                        "NOT",
                        "MINUS",
                        "PLUS",
                        "CONSTANT",
                        "CHAR_CONSTANT",
                        "STRING",
                    ],
                )
                is False
                and tmp == pos - 1
            ):
                context.new_error("SPC_BFR_PAR", context.peek_token(pos))
        return False

    def check_rnest(self, context, pos):
        if (
            context.history[-1] == "IsFuncDeclaration"
            or context.history[-1] == "IsFuncPrototype"
        ):
            return False
        tmp = pos + 1
        # Here is `)_`
        while (
            context.peek_token(tmp)
            and context.check_token(tmp, ["SPACE", "TAB"]) is True
        ):
            tmp += 1
        if context.check_token(tmp, "NEWLINE") is False:
            if (
                context.check_token(
                    tmp, lnests + rnests + ["SEMI_COLON", "PTR", "DOT", "INC", "DEC"]
                )
                is True
                and tmp != pos + 1
            ):
                context.new_error("NO_SPC_AFR_PAR", context.peek_token(pos))
            elif (
                context.check_token(
                    tmp,
                    lnests
                    + rnests
                    + [
                        "SEMI_COLON",
                        "PTR",
                        "DOT",
                        "INC",
                        "DEC",
                        "MINUS",
                        "MULT",
                        "BWISE_AND",
                        "IDENTIFIER",
                        "COMMA",
                        "STRING",
                        "CONSTANT",
                        "PLUS",
                    ],
                )
                is False
                and tmp == pos + 1
            ):
                context.new_error("SPC_AFTER_PAR", context.peek_token(pos))
        tmp = pos - 1
        # Here is `_)`
        while tmp > 0 and context.check_token(tmp, ["SPACE", "TAB"]) is True:
            tmp -= 1
        if context.check_token(tmp, "NEWLINE") is False:
            if (
                context.check_token(
                    tmp,
                    lnests
                    + rnests
                    + [
                        "SEMI_COLON",
                        "PTR",
                        "DOT",
                        "INC",
                        "DEC",
                        "MULT",
                        "BWISE_AND",
                        "IDENTIFIER",
                        "CONSTANT",
                    ],
                )
                is True
                and tmp != pos - 1
            ):
                context.new_error("NO_SPC_BFR_PAR", context.peek_token(pos))
        return False

    def check_suffix(self, context, pos):
        if pos + 1 < len(
            context.tokens[: context.tkn_scope]
        ) and not context.check_token(
            pos + 1, ["SPACE", "NEWLINE", "TAB"] + glued_operators + rnests
        ):
            context.new_error("SPC_AFTER_OPERATOR", context.peek_token(pos))
        if pos > 0 and context.peek_token(pos - 1).type == "SPACE":
            context.new_error("NO_SPC_BFR_OPR", context.peek_token(pos))

    def check_glued_prefix_and_suffix(self, context, pos):
        if pos > 0 and context.peek_token(pos - 1).type != "SPACE":
            if context.check_token(pos - 1, "TAB") is True:
                tmp = -1
                while context.check_token(pos + tmp, "TAB") is True:
                    tmp -= 1
                if (
                    context.check_token(
                        pos + tmp, ["NEWLINE", "ESCAPED_NEWLINE"] + glued_operators
                    )
                    is True
                ):
                    return False, 0
            context.new_error("SPC_BFR_OPERATOR", context.peek_token(pos))
        if (
            pos + 1 < len(context.tokens[: context.tkn_scope])
            and context.check_token(
                pos + 1,
                ["SPACE", "LPARENTHESIS", "LBRACKET", "LBRACE", "NEWLINE"]
                + glued_operators,
            )
            is False
        ):
            context.new_error("SPC_AFTER_OPERATOR", context.peek_token(pos))

    def check_prefix_and_suffix(self, context, pos):
        if (
            pos > 0
            and context.check_token(
                pos - 1, ["SPACE", "LPARENTHESIS", "LBRACKET"] + glued_operators
            )
            is False
        ):
            if context.check_token(pos - 1, "TAB") is True:
                tmp = -1
                while context.check_token(pos + tmp, "TAB") is True:
                    tmp -= 1
                if (
                    context.check_token(pos + tmp, ["NEWLINE", "ESCAPED_NEWLINE"])
                    is True
                ):
                    return False, 0
                # A line split on a backslash leaves no token behind: the
                # operator opens the new line, so nothing can precede it
                before = context.peek_token(pos + tmp)
                if before and before.lineno < context.peek_token(pos).lineno:
                    return False, 0
            if (
                context.check_token(pos - 1, "RPARENTHESIS")
                and context.parenthesis_contain(context.skip_nest_reverse(pos - 1))[0]
                == "cast"
            ):
                return False, 0
            context.new_error("SPC_BFR_OPERATOR", context.peek_token(pos))
        if (
            pos + 1 < len(context.tokens[: context.tkn_scope])
            and context.check_token(
                pos + 1,
                [
                    "SPACE",
                    "LPARENTHESIS",
                    "RPARENTHESIS",
                    "LBRACKET",
                    "RBRACKET",
                    "NEWLINE",
                    "COMMA",
                ]
                + spec_operators,
            )
            is False
        ):
            tmp = pos - 1
            while context.check_token(tmp, ["SPACE", "TAB"]):
                tmp -= 1
            if context.check_token(tmp, "RPARENTHESIS"):
                tmp = context.skip_nest_reverse(tmp)
                if context.parenthesis_contain(tmp)[0] != "cast":
                    context.new_error("SPC_AFTER_OPERATOR", context.peek_token(pos))
            elif context.check_token(tmp, glued_operators) is False and not (
                context.check_token(pos, ["PLUS", "MINUS"])
                and context.check_token(pos + 1, "CONSTANT")
            ):
                context.new_error("SPC_AFTER_OPERATOR", context.peek_token(pos))

    def check_glued_operator(self, context, pos):
        glued = [
            "LPARENTHESIS",
            "LBRACKET",
            "LBRACE",
        ]
        if context.check_token(pos + 1, ["SPACE", "TAB"]) is True:
            context.new_error("SPC_AFTER_OPERATOR", context.peek_token(pos))
        pos -= 1
        if (
            context.check_token(pos, glued + ["SPACE", "TAB"] + glued_operators)
            is False
        ):
            context.new_error("SPC_BFR_OPERATOR", context.peek_token(pos))
        while pos >= 0 and context.check_token(pos, ["SPACE", "TAB"]) is True:
            pos -= 1
            if pos >= 0 and context.check_token(pos, glued) is True:
                context.new_error("NO_SPC_BFR_OPR", context.peek_token(pos))

    def check_combined_op(self, context, pos):
        lpointer = [
            "SPACE",
            "TAB",
            "LPARENTHESIS",
            "LBRACKET",
            "MULT",
            "NOT",
            "RPARENTHESIS",
            "RBRACKET",
            "RBRACE",
            "MINUS",
            "PLUS",
            "BWISE_NOT",
            "BWISE_OR",
            "BWISE_AND",
            "BWISE_XOR",
        ]
        i = 0
        if context.check_token(pos, "MULT"):
            if context.check_token(pos - 1, lpointer) is False and (
                context.is_glued_operator(pos - 1) is True
            ):  # or context.check_token(pos - 1, c_operators) is False):
                context.new_error("SPC_BFR_POINTER", context.peek_token(pos))
            if context.check_token(pos + 1, ["SPACE", "TAB"]):
                context.new_error("SPC_AFTER_POINTER", context.peek_token(pos))
            i = 1
            while context.check_token(pos + i, ["MULT", "LPARENTHESIS"]):
                i += 1
                if context.check_token(pos + i, "SPACE"):
                    context.new_error("SPC_AFTER_POINTER", context.peek_token(pos + i))
                return i

    def run(self, context):
        """
        Some operators must be followed by a space,
        some must be only followed by a space,
        and the rest must be preceded and followed by a space.
        """
        i = 0
        while i < len(context.tokens[: context.tkn_scope]):
            if context.check_token(i, ["MULT", "BWISE_AND"]) is True:
                if context.is_operator(i) is False:
                    self.check_combined_op(context, i)
                    i += 1
                    continue
            if context.check_token(i, c_operators) is True:
                if context.is_glued_operator(i) is True:
                    self.check_glued_operator(context, i)
                else:
                    self.check_prefix_and_suffix(context, i)
                i += 1
                continue
            elif context.check_token(i, lnests) is True:
                self.check_lnest(context, i)
            elif context.check_token(i, rnests) is True:
                self.check_rnest(context, i)
            elif context.check_token(i, ps_operators) is True:
                self.check_prefix_and_suffix(context, i)
            elif context.check_token(i, gps_operators) is True:
                self.check_glued_prefix_and_suffix(context, i)
            elif context.check_token(i, s_operators) is True:
                self.check_suffix(context, i)
            elif (
                context.check_token(i, son_operators) is True
                and context.check_token(i + 1, "NEWLINE") is False
            ):
                self.check_suffix(context, i)
            elif context.check_token(i, p_operators) is True:
                self.check_prefix(context, i)
            i += 1
        return False, 0

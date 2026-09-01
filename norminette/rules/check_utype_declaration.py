from norminette.exceptions import CParsingError
from norminette.rules import Rule, Check

types = [
    "STRUCT",
    "ENUM",
    "UNION",
    "INT",
    "VOID",
    "CHAR",
    "UNSIGNED",
    "CONST",
    "DOUBLE",
    "LONG",
    "SHORT",
    "STATIC",
    "IDENTIFIER",
    "SPACE",
    "TAB",
]

utypes = ["STRUCT", "ENUM", "UNION"]


class CheckUtypeDeclaration(Rule, Check):
    depends_on = (
        "IsUserDefinedType",
    )

    def run(self, context):
        """
        User defined types must respect the following rules:
            - Struct names start with s_
            - Enum names start with e_
            - Union names start with u_
            - Typedef names start with t_
        """
        i = 0
        i = context.skip_ws(i)
        token = context.peek_token(i)
        if context.scope.name not in ("GlobalScope", "UserDefinedType"):
            context.new_error("TYPE_NOT_GLOBAL", token)
        if (
            context.file.type == ".c"
            and token.type in ("STRUCT", "UNION", "ENUM", "TYPEDEF")
            and context.scope not in ("UserDefinedType", "UserDefinedEnum")
        ):
            context.new_error(f"FORBIDDEN_{token.type}", token)
        is_td = False
        on_newline = False
        utype = None
        contain_full_def = False
        ids = []
        while context.check_token(i, ["SEMI_COLON"]) is False and i < len(
            context.tokens
        ):
            if context.check_token(i, ["SPACE", "TAB"]):
                pass
            if context.check_token(i, ["LPARENTHESIS"]) is True:
                val, tmp = context.parenthesis_contain(i)
                if val is None or val == "cast" or val == "var":
                    i = tmp
            if context.check_token(i, utypes) is True:
                utype = context.peek_token(i)
            if context.check_token(i, "TYPEDEF") is True:
                is_td = True
            if context.check_token(i, "LBRACKET") is True:
                i = context.skip_nest(i)
            if context.check_token(i, "IDENTIFIER") is True:
                if context.peek_token(i).value == "__attribute__":
                    i += 1
                    i = context.skip_ws(i)
                    i = context.skip_nest(i)
                    continue
                if (
                    context.check_token(i - 1, ["MULT", "BWISE_AND", "LPARENTHESIS"])
                    is True
                ):
                    tmp = i - 1
                    while (
                        context.check_token(
                            tmp - 1, ["MULT", "BWISE_AND", "LPARENTHESIS"]
                        )
                        is True
                        and context.is_operator(tmp) is False
                    ):
                        tmp -= 1
                    ids.append((context.peek_token(i), tmp))
                else:
                    ids.append((context.peek_token(i), i))
            if context.check_token(i, "LBRACE") is True:
                contain_full_def = True
                i = context.skip_nest(i)
            i += 1
        check = -1
        #        print (ids, utype, contain_full_def)
        if is_td is True and len(ids) < 2 and utype is not None:
            context.new_error("MISSING_TYPEDEF_ID", context.peek_token(0))
            return False, 0
        if contain_full_def is False and is_td is False and len(ids) > 1:
            check = -2
        else:
            check = -1
        if len(ids) == 0:
            return False, 0
        name = ids[0][0]
        loc = ids[check][1]
        if is_td is True:
            if not context.check_token(ids[check][1] - 1, ("SPACE", "TAB")):
                context.new_error("NO_TAB_BF_TYPEDEF", ids[check][0])
            if ids[check][0].value.startswith("t_") is False:
                context.new_error("USER_DEFINED_TYPEDEF", context.peek_token(loc))
            if utype is not None:
                if len(ids) > 1:
                    name = ids[0][0]
                else:
                    if context.debug >= 1:
                        pass
                    elif context.debug == 0:
                        raise CParsingError(
                            f"Error: {context.filename}: Could not parse structure line {context.peek_token(0).pos[0]}"
                        )
            loc = ids[0][1]
        else:
            loc = ids[0][1]
        # A typedef names the type twice, and the tag it introduces follows
        # the same rule as a bare one
        if is_td is False or len(ids) > 1:
            if (
                utype is not None
                and utype.type == "STRUCT"
                and name.value.startswith("s_") is False
            ):
                context.new_error("STRUCT_TYPE_NAMING", context.peek_token(loc))
            if (
                utype is not None
                and utype.type == "UNION"
                and name.value.startswith("u_") is False
            ):
                context.new_error("UNION_TYPE_NAMING", context.peek_token(loc))
            if (
                utype is not None
                and utype.type == "ENUM"
                and name.value.startswith("e_") is False
            ):
                context.new_error("ENUM_TYPE_NAMING", context.peek_token(loc))
        if is_td or (is_td is False and contain_full_def is False):
            tmp = ids[-1][1] - 1
            tabs = 0
            while (context.check_token(tmp, "TAB")) is True and tmp > 0:
                tabs += 1
                tmp -= 1
            # if tabs > 1:
            # context.new_error("TOO_MANY_TABS_TD", context.peek_token(tmp))
            if context.check_token(tmp, "SPACE") is True:
                context.new_error("SPACE_REPLACE_TAB", context.peek_token(tmp))
            tab_error = False
            can_nl_error = False
            while tmp > 0:
                if context.check_token(tmp, "RBRACE") is True:
                    can_nl_error = True
                    tmp = context.skip_nest_reverse(tmp)
                if context.check_token(tmp, "TAB") is True and on_newline is False:
                    tab_error = True
                if (
                    context.check_token(tmp, "NEWLINE") is True
                    and can_nl_error is False
                ):
                    context.new_error("NEWLINE_IN_DECL", context.peek_token(ids[-1][1]))
                    can_nl_error = True
                tmp -= 1
            if tab_error:
                context.new_error("TAB_REPLACE_SPACE", context.peek_token(tmp))
        if contain_full_def is False:
            i = 0
            i = ids[-1][1]
            if (
                context.check_token(i - 1, ["MULT", "BWISE_AND", "LPARENTHESIS"])
                is True
            ):
                i -= 1
                while (
                    context.check_token(i, ["MULT", "BWISE_AND", "LPARENTHESIS"])
                    is True
                    and context.is_operator(i) is False
                ):
                    i -= 1
            current_indent = context.peek_token(i).pos[1]
            if context.scope.vars_alignment == 0:
                context.scope.vars_alignment = current_indent
            elif context.scope.vars_alignment != current_indent:
                context.new_error("MISALIGNED_VAR_DECL", context.peek_token(0))
                return True, i
            return False, 0

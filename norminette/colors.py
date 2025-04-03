from typing import Optional

red = {
    "TOO_MANY_ARGS",
    "TOO_MANY_VARS_FUNC",
}
yellow = {
    "MIXED_SPACE_TAB",
    "BRACE_NEWLINE"
}
green = {
    "TOO_MANY_FUNCS",
}
blue = {
    "SPC_INSTEAD_TAB",
    "TAB_INSTEAD_SPC",
    "CONSECUTIVE_SPC",
    "CONSECUTIVE_WS",
    "SPC_BFR_OPERATOR",
    "SPC_AFTER_OPERATOR",
    "NO_SPC_BFR_OPR",
    "NO_SPC_AFR_OPR",
    "SPC_AFTER_PAR",
    "SPC_BFR_PAR",
    "NO_SPC_AFR_PAR",
    "NO_SPC_BFR_PAR",
    "SPC_AFTER_POINTER",
    "SPC_LINE_START",
    "SPC_BFR_POINTER",
    "SPACE_BEFORE_FUNC",
    "TOO_MANY_TABS_FUNC",
    "TOO_MANY_TABS_TD",
    "MISSING_TAB_FUNC",
    "MISSING_TAB_VAR",
    "TOO_MANY_TAB_VAR",
    "LINE_TOO_LONG",
    "EXP_PARENTHESIS",
}
pink = {
    "WRONG_SCOPE_COMMENT",
    "COMMENT_ON_INSTR",
}
grey = {
    "INVALID_HEADER",
    "WRONG_SCOPE_COMMENT",
}

_color_table = {
    "91": red,
    "92": green,
    "93": yellow,
    "94": blue,
    "95": pink,
    "97": grey,
}


def error_color(name: str) -> Optional[str]:
    for color, table in _color_table.items():
        if name in table:
            return color
    return None

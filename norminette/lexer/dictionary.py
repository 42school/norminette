""" Dictionary that correlates lexeme with token """

trigraphs = {
    "??<": '{',
    "??>": '}',
    "??(": '[',
    "??)": ']',
    "??=": '#',
    "??/": '\\',
    "??'": '^',
    "??!": '|',
    "??-": '~',
}

digraphs = {
    "<%": '{',
    "%>": '}',
    "<:": '[',
    ":>": ']',
    "%:": '#',
}

keywords = {
    # C reserved keywords #
    "auto": "AUTO",
    "break": "BREAK",
    "case": "CASE",
    "char": "CHAR",
    "const": "CONST",
    "continue": "CONTINUE",
    "default": "DEFAULT",
    "do": "DO",
    "double": "DOUBLE",
    "else": "ELSE",
    "enum": "ENUM",
    "extern": "EXTERN",
    "float": "FLOAT",
    "for": "FOR",
    "goto": "GOTO",
    "if": "IF",
    "int": "INT",
    "long": "LONG",
    "register": "REGISTER",
    "return": "RETURN",
    "short": "SHORT",
    "signed": "SIGNED",
    "sizeof": "SIZEOF",
    "static": "STATIC",
    "struct": "STRUCT",
    "switch": "SWITCH",
    "typedef": "TYPEDEF",
    "union": "UNION",
    "unsigned": "UNSIGNED",
    "void": "VOID",
    "volatile": "VOLATILE",
    "while": "WHILE",
    "inline": "INLINE",
    "NULL": "NULL",
    "restrict": "RESTRICT",
    "_Alignas": "ALIGNAS",
}

"""
__FILE__ ?add?
__LINE__ ?add?
__DATE__ ?add?
__TIME__ ?add?
__TIMESTAMP__ ?add?
"""

operators = {
    ">>=": "RIGHT_ASSIGN",
    "<<=": "LEFT_ASSIGN",
    "+=": "ADD_ASSIGN",
    "-=": "SUB_ASSIGN",
    "*=": "MUL_ASSIGN",
    "/=": "DIV_ASSIGN",
    "%=": "MOD_ASSIGN",
    "&=": "AND_ASSIGN",
    "^=": "XOR_ASSIGN",
    "|=": "OR_ASSIGN",
    "<=": "LESS_OR_EQUAL",
    ">=": "GREATER_OR_EQUAL",
    "==": "EQUALS",
    "!=": "NOT_EQUAL",
    "=": "ASSIGN",
    ";": "SEMI_COLON",
    ":": "COLON",
    ",": "COMMA",
    ".": "DOT",
    "!": "NOT",
    "-": "MINUS",
    "+": "PLUS",
    "*": "MULT",
    "/": "DIV",
    "%": "MODULO",
    "<": "LESS_THAN",
    ">": "MORE_THAN",
    "...": "ELLIPSIS",
    "++": "INC",
    "--": "DEC",
    "->": "PTR",
    "&&": "AND",
    "||": "OR",
    "^": "BWISE_XOR",
    "|": "BWISE_OR",
    "~": "BWISE_NOT",
    "&": "BWISE_AND",
    ">>": "RIGHT_SHIFT",
    "<<": "LEFT_SHIFT",
    "?": "TERN_CONDITION",
    "#": "HASH",
}

brackets = {
    "{": "LBRACE",
    "}": "RBRACE",
    "(": "LPARENTHESIS",
    ")": "RPARENTHESIS",
    "[": "LBRACKET",
    "]": "RBRACKET",
}

__all__ = ["brackets", "operators", "keywords"]

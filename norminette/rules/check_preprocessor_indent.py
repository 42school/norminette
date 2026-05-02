from norminette.rules import Rule, Check
from norminette.scope import GlobalScope

ARGUMENTED_PREPROCESSORS = (
    "include",
    "import",
    "if",  # just in case
    None,  # "if" is a special case ...
    "ifdef",
    "ifndef",
    "elif",
    "error",
    "pragma",
    "undef",
    "define",
)


class CheckPreprocessorIndent(Rule, Check):
    depends_on = (
        "IsPreprocessorStatement",
    )

    def run(self, context):
        """
        Preprocessor statements must be indented by an additionnal space for each #ifdef/#ifndef/#if
        statement.
        Structure is `#{indentation}preproc_statement`
        Preprocessor must always be at the start of the line
        Argumented preprocessor statements must have a space between the identifier and the argument
        """
        i = context.skip_ws(0)

        hash_ = context.peek_token(i)
        if hash_ and hash_.line_column != 1:
            context.new_error("PREPROC_START_LINE", hash_)
        if not isinstance(context.scope, GlobalScope):
            context.new_error("PREPOC_ONLY_GLOBAL", hash_)
        i += 1

        # Empty preprocessor statement (only #)
        k = context.skip_ws(i, comment=True)
        if context.check_token(k, "NEWLINE"):
            return

        n = context.skip_ws(i)
        spaces = 0
        while context.check_token(i, "SPACE"):
            i += 1
            spaces += 1
        if context.check_token(i, "TAB"):
            context.new_error("TAB_REPLACE_SPACE", context.peek_token(i))
        while context.check_token(i, "TAB"):
            i += 1
            spaces += 1
        i = n

        # Check indentation
        indent = context.preproc.indent
        if context.check_token(i, ("IF", "ELSE")):
            indent -= 1
        else:
            t = context.peek_token(i)
            if t and t.type == "IDENTIFIER" and t.value.upper() in ("IFNDEF", "IFDEF", "ELIF"):
                indent -= 1
        indent = max(0, indent)
        if spaces > indent:
            context.new_error("TOO_MANY_WS", hash_)
        if spaces < indent:
            context.new_error("PREPROC_BAD_INDENT", hash_)

        # Check spacing after preproc identifier
        if (
            context.check_token(i, ("IDENTIFIER", "IF"))
            and context.peek_token(i).value in ARGUMENTED_PREPROCESSORS
        ):
            i += 1
            # BUG: #error/warning with a "comment" (`#error // Hello`) will be
            # ignored, but it's not a big deal.
            n = context.skip_ws(i, comment=True)
            if context.check_token(n, "NEWLINE"):
                return
            # The idea is to avoid:
            # - `#include"libft.h"`      (no space)
            # - `#include 	 "libft.h"`  (tab)
            # - `#include  "libft.h"`    (two spaces)
            # Note that only `#include "libft.h"` is valid and we also check
            # for `ifdef`, `ifndef`, etc.
            if not context.check_token(i, ("SPACE", "TAB")):
                context.new_error("PREPROC_NO_SPACE", context.peek_token(i))
            j = i
            while context.check_token(i, "SPACE"):
                i += 1
            if context.check_token(i, "TAB"):
                context.new_error("TAB_REPLACE_SPACE", context.peek_token(i))
            if context.skip_ws(j) - j > 1:
                context.new_error("CONSECUTIVE_WS", context.peek_token(j))

from norminette.errors import Error, Highlight
from norminette.rules import Rule, Check


class CheckNewlineEof(Rule, Check, runs_on_end=True, runs_on_rule=False):
    def run(self, context):
        """
        A file must end with a newline
        """
        source = context.file.source
        if source == "" or source.endswith("\n"):
            return False, 0
        lines = source.split("\n")
        context.errors.add(
            Error.from_name(
                "NO_NEWLINE_EOF",
                highlights=[Highlight(len(lines), len(lines[-1]) + 1)],
            )
        )
        return False, 0

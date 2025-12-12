from norminette.rules import Rule, Check
from norminette.errors import Error


class CheckLineLen(Rule, Check):
    runs_on_rule = False
    runs_on_end = True

    def run(self, context):
        for lineno, line in enumerate(context.file, start=1):
            if len(line.translated) <= 80:
                continue
            error = Error.from_name("LINE_TOO_LONG")
            error.add_highlight(lineno, 81, length=len(line.translated) - 80)
            context.file.errors.add(error)

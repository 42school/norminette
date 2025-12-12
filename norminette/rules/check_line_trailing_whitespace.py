from norminette.rules import Rule, Check
from norminette.errors import Error


class CheckLineTrailingWhitespace(Rule, Check):
    runs_on_rule = False
    runs_on_end = True

    def run(self, context):
        for lineno, line in enumerate(context.file, start=1):
            offset = 0
            for char in reversed(line.translated):
                if char not in " \t":
                    break
                offset += 1
            error = None
            if line.translated and line.translated.strip(" \t") == '':
                error = Error.from_name("SPACE_EMPTY_LINE")
                error.add_highlight(lineno, 1, length=len(line.translated))
            elif offset != 0:
                error = Error.from_name("SPC_BEFORE_NL")
                error.add_highlight(lineno, len(line.translated) - offset + 1, length=offset)
            if error:
                context.file.errors.add(error)

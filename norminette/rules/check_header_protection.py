from norminette.errors import Error, Highlight
from norminette.rules import Rule, Check


class CheckHeaderProtection(Rule, Check, runs_on_end=True, runs_on_rule=False):
    def run(self, context):
        """
        A header file must be protected from double inclusions
        """
        if context.file.type != ".h" or context.protected:
            return False, 0
        if context.file.source.strip() == "":
            return False, 0
        context.errors.add(
            Error.from_name("HEADER_PROT_MISSING", highlights=[Highlight(1, 1)])
        )
        return False, 0

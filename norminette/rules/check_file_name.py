import os
import re

from norminette.errors import Error, Highlight
from norminette.rules import Rule, Check

allowed = re.compile(r"[a-z0-9_]+")


class CheckFileName(Rule, Check, runs_on_end=True, runs_on_rule=False):
    def run(self, context):
        """
        File and directory names hold lowercases, digits and underscores
        """
        parts = [context.file.name]
        path = context.file.path
        if not os.path.isabs(path):
            # Only the directories the caller named, never the ones above
            parts += os.path.dirname(path).split(os.sep)
        for part in parts:
            if part in ("", ".", ".."):
                continue
            if allowed.fullmatch(part) is None:
                context.errors.add(
                    Error.from_name("FORBIDDEN_CHAR_FILE", highlights=[Highlight(1, 1)])
                )
                return False, 0
        return False, 0

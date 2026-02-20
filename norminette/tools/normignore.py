import os
import pathspec


class NormIgnoreSpec:
    def __init__(self, cwd):
        self.spec = self._load(cwd)
        self.filepath = os.path.join(os.getcwd(), ".normignore")

    def _load(self, cwd):
        try:
            with open(os.path.join(cwd, ".normignore")) as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            return None
        except PermissionError:
            print("Warning: unable to access normignore file")
            return None

        return pathspec.PathSpec.from_lines(
            "gitignore",
            lines
        )

    def is_ignored(self, target):
        if not self.spec:
            return False
        return self.spec.match_file(target)

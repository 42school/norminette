import os
from typing import Optional

from norminette.errors import Errors


class File:
    def __init__(self, path: str, source: Optional[str] = None) -> None:
        self.path = path
        self._source = source

        self.errors = Errors()
        self.basename = os.path.basename(path)
        self.name, self.type = os.path.splitext(self.basename)

    @property
    def source(self) -> str:
        if self._source is None:
            with open(self.path, encoding="utf-8", errors="replace") as file:
                self._source = file.read()
        return self._source

    def __repr__(self) -> str:
        return f"<File {self.path!r}>"

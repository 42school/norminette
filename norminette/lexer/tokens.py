from typing import Optional, Tuple
from dataclasses import dataclass, field


@dataclass(eq=True, repr=True)
class Token:
    type: str
    pos: Tuple[int, int]
    value: Optional[str] = field(default=None)

    @property
    def length(self) -> int:
        return len(self.value or '')

    @property
    def lineno(self) -> int:
        return self.pos[0]

    @property
    def column(self) -> int:
        return self.pos[1]

    @property
    def line_column(self):
        return self.pos[1]

    def __str__(self):
        """
        Token representation for debugging, using the format <TYPE=value>
        or simply <TYPE> when value is None
        """
        r = f"<{self.type}={self.value}>" if self.value else f"<{self.type}>"
        return r

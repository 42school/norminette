import os
from typing import Optional, Any, Sequence, overload, Tuple
from functools import cached_property

from norminette.errors import Errors
from norminette.exceptions import MaybeInfiniteLoop
from norminette.utils import max_loop_iterations


class _Line:
    def __init__(self, inner: str, /) -> None:
        self._inner = inner

    @property
    def translated(self) -> str:
        result = ''
        for char in self._inner:
            if char == '\n':
                break
            if char == '\t':
                char = ' ' * (4 - len(result) % 4)
            result += char
        return result

    def endswith(self, value: Sequence[str], /) -> bool:
        if isinstance(value, str):
            value = value,
        for value in value:
            if self._inner.endswith('\n'):
                value += '\n'
            if self._inner.endswith(value):
                return True
        return False


class File:
    def __init__(self, path: str, source: Optional[str] = None) -> None:
        self.path = path
        self._source = source
        self._line_to_index = {}

        self.errors = Errors()
        self.basename = os.path.basename(path)
        self.name, self.type = os.path.splitext(self.basename)

    @cached_property
    def source(self) -> str:
        if self._source is None:
            with open(self.path) as file:
                self._source = file.read()
        lineno = 1
        offset = None
        self._line_to_index = {1: 0}
        for _ in range(max_loop_iterations):
            offset = self._source.find('\n', offset)
            if offset == -1:
                break
            offset += 1
            lineno += 1
            self._line_to_index[lineno] = offset
        else:
            raise MaybeInfiniteLoop()
        return self._source

    def _line(self, lineno: int, /) -> Optional[_Line]:
        if lineno not in self._line_to_index:
            return
        offset = self._line_to_index[lineno]
        ending = self.source.find('\n', offset)
        if ending == -1:
            ending = len(self.source)
        else:
            ending += 1
        return _Line(self.source[offset:ending])

    def __iter__(self):
        lineno = 1
        while (line := self._line(lineno)) is not None:
            yield line
            lineno += 1
        return

    def __repr__(self) -> str:
        return f"<File {self.path!r}>"

    @overload
    def __getitem__(self, item: int) -> str: ...
    @overload
    def __getitem__(self, item: Tuple[int]) -> _Line: ...

    def __getitem__(self, item: Any):
        if isinstance(item, int):
            return self.source[item]
        if isinstance(item, tuple):
            if len(item) == 1:
                lineno = item[0]
                return self._line(lineno)
            # if len(item) == 2:
            #     lineno, column = item
            #     return self._line_to_index[lineno + column]
        raise TypeError(...)

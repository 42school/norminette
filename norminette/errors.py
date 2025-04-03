from __future__ import annotations

import os
import json
from dataclasses import dataclass, field, asdict
from typing import (
    TYPE_CHECKING,
    Sequence,
    Union,
    Literal,
    Optional,
    List,
    overload,
    Any,
    Type,
)

from norminette.colors import error_color
from norminette.norm_error import errors as errors_dict

if TYPE_CHECKING:
    from norminette.lexer import Token
    from norminette.file import File

ErrorLevel = Literal["Error", "Notice"]


@dataclass
class Highlight:
    lineno: int
    column: int
    length: Optional[int] = field(default=None)
    hint: Optional[str] = field(default=None)

    @classmethod
    def from_token(
        cls,
        token: Token,
        *,
        hint: Optional[str] = None,
    ) -> Highlight:
        return cls(token.lineno, token.column, token.unsafe_length, hint)

    def __lt__(self, other: Any) -> bool:
        assert isinstance(other, Highlight)
        if self.lineno == other.lineno:
            if self.column == other.column:
                return len(self.hint or '') > len(other.hint or '')
            return self.column > other.column
        return self.lineno > other.lineno


@dataclass
class Error:
    name: str
    text: str
    level: ErrorLevel = field(default="Error")
    highlights: List[Highlight] = field(default_factory=list)

    @classmethod
    def from_name(cls: Type[Error], /, name: str, **kwargs) -> Error:
        return cls(name, errors_dict[name], **kwargs)

    def __lt__(self, other: Any) -> bool:
        assert isinstance(other, Error)
        if not self.highlights:
            return bool(other.highlights) or self.name > other.name
        if not other.highlights:
            return bool(self.highlights) or other.name > self.name
        ah, bh = min(self.highlights), min(other.highlights)
        if ah.column == bh.column and ah.lineno == bh.lineno:
            return self.name < other.name
        return (ah.lineno, ah.column) < (bh.lineno, bh.column)

    @overload
    def add_highlight(
        self,
        lineno: int,
        column: int,
        length: Optional[int] = None,
        hint: Optional[str] = None,
    ) -> None: ...
    @overload
    def add_highlight(self, highlight: Highlight, /) -> None: ...

    def add_highlight(self, *args, **kwargs) -> None:
        if len(args) == 1:
            highlight, = args
        else:
            highlight = Highlight(*args, **kwargs)
        self.highlights.append(highlight)


class Errors:
    __slots__ = "_inner"

    def __init__(self) -> None:
        self._inner: List[Error] = []

    def __repr__(self) -> str:
        return repr(self._inner)

    def __len__(self) -> int:
        return len(self._inner)

    def __iter__(self):
        self._inner.sort()
        return iter(self._inner)

    @overload
    def add(self, error: Error) -> None:
        """Add an `Error` instance to the errors.
        """
        ...

    @overload
    def add(self, name: str, *, level: ErrorLevel = "Error", highlights: List[Highlight] = ...) -> None:
        """Builds an `Error` instance from a name in `errors_dict` and adds it to the errors.

        ```python
        >>> errors.add("TOO_MANY_LINES")
        >>> errors.add("INVALID_HEADER")
        >>> errors.add("GLOBAL_VAR_DETECTED", level="Notice")
        ```
        """
        ...

    @overload
    def add(
        self,
        /,
        name: str,
        text: str,
        *,
        level: ErrorLevel = "Error",
        highlights: List[Highlight] = ...,
    ) -> None:
        """Builds an `Error` instance and adds it to the errors.

        ```python
        >>> errors.add("BAD_IDENTATION", "You forgot an column here")
        >>> errors.add("CUSTOM_ERROR", f"name {not_defined!r} is not defined. Did you mean: {levenshtein_distance}?")
        >>> errors.add("NOOP", "Empty if statement", level="Notice")
        ```
        """
        ...

    def add(self, *args, **kwargs) -> None:
        kwargs.setdefault("level", "Error")
        error = None
        if len(args) == 1:
            error = args[0]
            if isinstance(error, str):
                error = Error.from_name(error, **kwargs)
        if len(args) == 2:
            error = Error(*args, **kwargs)
        assert isinstance(error, Error), "bad function call"
        return self._inner.append(error)

    @property
    def status(self) -> Literal["OK", "Error"]:
        return "OK" if all(it.level == "Notice" for it in self._inner) else "Error"

    def append(self, *args, **kwargs):
        """Deprecated alias for `.add(...)`, kept for backward compatibility.

        Use `.add(...)` instead.
        """
        return self.add(*args, **kwargs)


class _formatter:
    name: str

    def __init__(self, files: Union[File, Sequence[File]], **options) -> None:
        if not isinstance(files, Sequence):
            files = [files]
        self.files = files
        self.options = options

    def __init_subclass__(cls) -> None:
        cls.name = cls.__name__.rstrip("ErrorsFormatter").lower()


class HumanizedErrorsFormatter(_formatter):
    @property
    def use_colors(self) -> bool:
        return self.options.get("use_colors", True)

    def _colorize_error_text(self, error: Error) -> str:
        color = error_color(error.name)
        if not self.use_colors or not color:
            return error.text
        return f"\x1b[{color}m{error.text}\x1b[0m"

    def __str__(self) -> str:
        output = ''
        for file in self.files:
            output += f"{file.basename}: {file.errors.status}!"
            for error in file.errors:
                highlight = error.highlights[0]
                error_text = self._colorize_error_text(error)
                output += f"\n{error.level}: {error.name:<20} "
                output += f"(line: {highlight.lineno:>3}, col: {highlight.column:>3}):\t{error_text}"
            output += '\n'
        return output


class JSONErrorsFormatter(_formatter):
    def __str__(self):
        files = []
        for file in self.files:
            files.append({
                "path": os.path.abspath(file.path),
                "status": file.errors.status,
                "errors": tuple(map(asdict, file.errors)),
            })
        output = {
            "files": files,
        }
        return json.dumps(output, separators=(',', ':')) + '\n'


formatters = (
    JSONErrorsFormatter,
    HumanizedErrorsFormatter,
)

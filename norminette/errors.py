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

from norminette.norm_error import NormError, NormWarning, errors as errors_dict

if TYPE_CHECKING:
    from norminette.lexer import Token
    from norminette.file import File


@dataclass
class Highlight:
    lineno: int
    column: int
    length: Optional[int] = field(default=None)
    hint: Optional[str] = field(default=None)

    def __lt__(self, other: Any) -> bool:
        assert isinstance(other, Highlight)
        if self.lineno == other.lineno:
            if self.column == other.column:
                return len(self.hint or '') > len(other.hint or '')
            return self.column > other.column
        return self.lineno > other.lineno

    @classmethod
    def from_token(cls, token: Token, /) -> Highlight:
        return cls(
            lineno=token.lineno,
            column=token.column,
            length=token.length,
        )


@dataclass
class Error:
    name: str
    text: str
    level: Literal["Error", "Notice"] = field(default="Error")
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
    @overload
    def add_highlight(self, token: Token, /) -> None: ...

    def add_highlight(self, *args, **kwargs) -> None:
        if len(args) == 1:
            highlight, = args
            if not isinstance(highlight, Highlight):  # highlight is Token
                highlight = Highlight.from_token(highlight)
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
    def add(self, name: str, *, level: Literal["Error", "Notice"] = "Error", highlights: List[Highlight] = ...) -> None:
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
        level: Literal["Error", "Notice"] = "Error",
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

    def append(self, value: Union[NormError, NormWarning]) -> None:
        # TODO Remove NormError and NormWarning since it does not provide `length` data
        assert isinstance(value, (NormError, NormWarning))
        level = "Error" if isinstance(value, NormError) else "Notice"
        error = Error(value.errno, value.error_msg, level, highlights=[
            Highlight(value.line, value.col, None),
        ])
        self._inner.append(error)


class _formatter:
    name: str

    def __init__(self, files: Union[File, Sequence[File]]) -> None:
        if not isinstance(files, Sequence):
            files = [files]
        self.files = files

    def __init_subclass__(cls) -> None:
        name = cls.__name__
        if name.endswith(suffix := "ErrorsFormatter"):
            name = name[:-len(suffix)]
        cls.name = name.lower()


class HumanizedErrorsFormatter(_formatter):
    def __str__(self) -> str:
        output = ''
        for file in self.files:
            for error in file.errors:
                highlight = error.highlights[0]
                # Location
                output += f"\x1b[;97m{file.path}:{highlight.lineno}:{highlight.column}\x1b[0m"
                output += ' ' + error.name
                if not highlight.length:
                    output += ' ' + error.text
                if highlight.length:
                    # Line
                    output += f"\n {highlight.lineno:>5} | {file[highlight.lineno,].translated}"
                    # Arrow
                    output += "\n       | " + ' ' * (highlight.column - 1)
                    output += f"\x1b[0;91m{'^' * (highlight.length or 0)} {highlight.hint or error.text}\x1b[0m"
                output += '\n'
        return output


class ShortErrorsFormatter(_formatter):
    def __str__(self) -> str:
        output = ''
        for file in self.files:
            output += f"{file.basename}: {file.errors.status}!"
            for error in file.errors:
                highlight = error.highlights[0]
                output += f"\n{error.level}: {error.name:<20} "
                output += f"(line: {highlight.lineno:>3}, col: {highlight.column:>3}):\t{error.text}"
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
    ShortErrorsFormatter,
    HumanizedErrorsFormatter,
)

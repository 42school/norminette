from __future__ import annotations

import os
import json
import collections
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

    def __lt__(self, other: Any) -> bool:
        assert isinstance(other, Highlight)
        if self.lineno == other.lineno:
            if self.column == other.column:
                return len(self.hint or '') > len(other.hint or '')
            return self.column < other.column
        return self.lineno < other.lineno

    @classmethod
    def from_token(
        cls,
        token: Token,
        /,
        hint: str | None = None,
    ) -> Highlight:
        return cls(
            lineno=token.lineno,
            column=token.column,
            length=token.unsafe_length,
            hint=hint,
        )

    @staticmethod
    def merge(highlights: list[Highlight]) -> list[Highlight]:
        if len(highlights) < 2:
            return highlights

        highlights.sort()

        drop = []

        last = None
        for index, highlight in enumerate(highlights):
            if last is None:
                last = highlight
                continue

            last_len = last.length or 0
            curr_len = highlight.length or 0
            if (last.column + last_len) >= highlight.column and not last.hint and not highlight.hint:
                last.length = last_len + curr_len
                drop.append(index)
            else:
                last = highlight

        for index in reversed(drop):
            del highlights[index]

        return highlights

    @staticmethod
    def unpack(highlights: list[Highlight]):
        result = []

        by_line = collections.defaultdict(list)
        for highlight in highlights:
            by_line[highlight.lineno].append(highlight)
        for lineno, hls in by_line.items():
            rest = []
            for highlight in hls:
                if highlight.hint:
                    result.append((lineno, [highlight]))
                else:
                    rest.append(highlight)
            if rest:
                result.append((lineno, rest))

        return result


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
        name = cls.__name__
        if name.endswith(suffix := "ErrorsFormatter"):
            name = name[:-len(suffix)]
        cls.name = name.lower()

    @property
    def use_colors(self) -> bool:
        return self.options.get("use_colors", True)

    def _colorize_error_text(self, error: Error) -> str:
        color = error_color(error.name)
        if not self.use_colors or not color:
            return error.text
        return f"\x1b[{color}m{error.text}\x1b[0m"


class Frame:
    __slots__ = "file", "error", "colorize"

    def __init__(self, file: File, error: Error, *, colorize: bool = False) -> None:
        self.file = file
        self.error = error
        self.colorize = colorize

    @property
    def _path(self) -> str:
        items: list[str | int] = [self.file.path]
        for highlight in self.error.highlights:
            items.append(highlight.lineno)
            items.append(highlight.column)
            break
        path = ':'.join(map(str, items))
        return path if not self.colorize else f"\x1b[;97m{path}\x1b[0m"

    def _build_code_sublines(self, highlights: list[Highlight]):
        subline = ''
        hint = ''
        for highlight in highlights:
            if highlight.hint:
                if hint:
                    hint += ', '
                hint += highlight.hint
            if len(subline) < highlight.column - 1:
                subline += ' ' * (highlight.column - 1 - len(subline))
            subline += '^' * (highlight.length or 1)
        if hint:
            subline += f"  \x1b[3;94m{hint}\x1b[0m"
        yield subline

    def _build_code_lines(self, lineno: int, arrows: List[Highlight]):
        assert arrows, "No highlights to build line from"

        arrows = Highlight.merge(arrows)
        arrows = Highlight.unpack(arrows)
        print("Unpacked", arrows)

        for lineno, highlights in arrows:  # type: ignore
            yield f" {lineno:>5} | {self.file[lineno,].translated}"

            for subline in self._build_code_sublines(highlights):
                yield f" {' ':>5} | \x1b[;91m{subline}\x1b[0m"

    def __str__(self):
        lines = []
        lines.append(self._path + f" {self.error.name}")

        last = None
        arrows = []
        for highlight in sorted(self.error.highlights):
            if highlight.length is None:
                continue
            if last and last.lineno == highlight.lineno:
                arrows.append(highlight)
            else:
                if last:
                    code = self._build_code_lines(last.lineno, arrows)
                    lines.extend(code)
                arrows = [highlight]
            last = highlight
        if last:
            code = self._build_code_lines(last.lineno, arrows)
            lines.extend(code)

        if len(lines) == 1:
            lines[0] += f" {self.error.text}"
        else:
            lines[0] += f" \x1b[0;91m{self.error.text}\x1b[0m"

        return '\n'.join(lines)


class HumanizedErrorsFormatter(_formatter):
    def __str__(self) -> str:
        output = ''
        for file in self.files:
            for error in file.errors:
                frame = Frame(file, error, colorize=self.use_colors)
                output += str(frame) + '\n'
        return output


class ShortErrorsFormatter(_formatter):
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
    ShortErrorsFormatter,
    HumanizedErrorsFormatter,
)

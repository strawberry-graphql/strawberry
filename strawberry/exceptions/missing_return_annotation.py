import inspect
import itertools
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from backports.cached_property import cached_property

from .exception import ExceptionSource, StrawberryException
from .utils.getsource import getsourcelines


if TYPE_CHECKING:
    from rich.console import RenderableType

    from strawberry.types.fields.resolver import StrawberryResolver


class MissingReturnAnnotationError(StrawberryException):
    """The field is missing the return annotation"""

    documentation_url = "https://errors.strawberry.rocks/missing-return-annotation"

    def __init__(self, field_name: str, resolver: "StrawberryResolver"):
        self.resolver = resolver

        self.message = (
            f'Return annotation missing for field "{field_name}", '
            "did you forget to add it?"
        )
        self.rich_message = (
            "[bold red]Missing annotation for field "
            f"`[underline]{self.resolver.name}[/]`"
        )

        self.suggestion = (
            "To fix this error you can add an annotation, "
            f"like so [italic]`def {self.resolver.name} -> str:`"
        )

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.resolver is None:
            return None

        resolver = self.resolver.wrapped_func

        source_file = inspect.getsourcefile(resolver)  # type: ignore

        if source_file is None:
            return None

        source_lines, start_line = getsourcelines(resolver)

        resolver_line, resolver_line_text = next(
            (index, line)
            for index, line in enumerate(source_lines)
            if f"def {self.resolver.name}" in line
        )
        error_column = sum(
            1 for _ in itertools.takewhile(str.isspace, resolver_line_text)
        )

        return ExceptionSource(
            path=Path(source_file),
            code="".join(source_lines),
            start_line=start_line,
            error_line=start_line + resolver_line,
            end_line=start_line + len(source_lines),
            error_column=error_column,
        )

    @property
    def __rich_body__(self) -> "RenderableType":
        assert self.exception_source

        error_line = self.exception_source.error_line

        prefix = " " * (self.exception_source.error_column + len("def "))
        caret = "^" * len(self.resolver.name)

        message = f"{prefix}[bold]{caret}[/] resolver missing annotation"

        line_annotations = {error_line: message}

        return self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

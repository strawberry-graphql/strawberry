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
        message = (
            f'Return annotation missing for field "{field_name}", '
            "did you forget to add it?"
        )
        self.resolver = resolver

        super().__init__(message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.resolver is None:
            return None

        resolver = self.resolver.wrapped_func

        source_file = inspect.getsourcefile(resolver)  # type: ignore

        if source_file is None:
            return None

        source_lines, line = getsourcelines(resolver)

        return ExceptionSource(
            path=Path(source_file), code="".join(source_lines), line=line
        )

    def __rich__(self) -> Optional["RenderableType"]:
        from rich.box import SIMPLE
        from rich.console import Group
        from rich.panel import Panel

        if not self.exception_source:
            return None

        lines = self.exception_source.code.splitlines()
        resolver_line = next(
            line for line in lines if f"def {self.resolver.name}" in line
        )

        column = sum(1 for _ in itertools.takewhile(str.isspace, resolver_line))

        source_file = self.exception_source.path
        relative_path = self.exception_source.path_relative_to_cwd
        error_line = self.exception_source.line + lines.index(resolver_line)

        prefix = " " * (column + len("def "))
        caret = "^" * len(self.resolver.name)

        message = f"{prefix}[bold]{caret}[/] resolver missing annotation"

        line_annotations = {error_line: message}

        code = self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

        header = (
            "[bold red]Missing annotation for field "
            f"`[underline]{self.resolver.name}[/]` "
            f"in [white][link=file://{source_file}]{relative_path}:{error_line}"
        )

        footer = (
            "To fix this error you can add an annotation, "
            f"like so [italic]`def {self.resolver.name} -> str:`"
            "\n\n"
            "Read more about this error on [bold underline]"
            f"[link={self.documentation_url}]{self.documentation_url}"
        )

        content = (
            header,
            "",
            code,
            "",
            *footer.splitlines(),
        )

        return Panel.fit(
            Group(*content),  # type: ignore
            box=SIMPLE,
        )

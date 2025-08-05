from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Optional

from strawberry.utils.str_converters import to_kebab_case

if TYPE_CHECKING:
    from rich.console import RenderableType

    from .exception_source import ExceptionSource


class UnableToFindExceptionSource(Exception):
    """Internal exception raised when we can't find the exception source."""


class StrawberryException(Exception, ABC):
    message: str
    rich_message: str
    suggestion: str
    annotation_message: str

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

    @property
    def documentation_path(self) -> str:
        return to_kebab_case(self.__class__.__name__.replace("Error", ""))

    @property
    def documentation_url(self) -> str:
        prefix = "https://errors.strawberry.rocks/"

        return prefix + self.documentation_path

    @cached_property
    @abstractmethod
    def exception_source(self) -> Optional[ExceptionSource]:
        return None

    @property
    def __rich_header__(self) -> RenderableType:
        return f"[bold red]error: {self.rich_message}"

    @property
    def __rich_body__(self) -> RenderableType:
        assert self.exception_source

        return self._get_error_inline(self.exception_source, self.annotation_message)

    @property
    def __rich_footer__(self) -> RenderableType:
        return (
            f"{self.suggestion}\n\n"
            "Read more about this error on [bold underline]"
            f"[link={self.documentation_url}]{self.documentation_url}"
        ).strip()

    def __rich__(self) -> Optional[RenderableType]:
        from rich.box import SIMPLE
        from rich.console import Group
        from rich.panel import Panel

        if self.exception_source is None:
            raise UnableToFindExceptionSource from self

        content = (
            self.__rich_header__,
            "",
            self.__rich_body__,
            "",
            "",
            self.__rich_footer__,
        )

        return Panel.fit(
            Group(*content),
            box=SIMPLE,
        )

    def _get_error_inline(
        self, exception_source: ExceptionSource, message: str
    ) -> RenderableType:
        source_file = exception_source.path
        relative_path = exception_source.path_relative_to_cwd
        error_line = exception_source.error_line

        from rich.console import Group

        from .syntax import Syntax

        path = f"[white]     @ [link=file://{source_file}]{relative_path}:{error_line}"

        prefix = " " * exception_source.error_column
        caret = "^" * (
            exception_source.error_column_end - exception_source.error_column
        )

        message = f"{prefix}[bold]{caret}[/] {message}"

        error_line = exception_source.error_line
        line_annotations = {error_line: message}

        return Group(
            path,
            "",
            Syntax(
                code=exception_source.code,
                highlight_lines={error_line},
                line_offset=exception_source.start_line - 1,
                line_annotations=line_annotations,
                line_range=(
                    exception_source.start_line - 1,
                    exception_source.end_line,
                ),
            ),
        )

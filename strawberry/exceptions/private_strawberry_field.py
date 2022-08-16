from typing import TYPE_CHECKING, Optional, Type

from backports.cached_property import cached_property

from .exception import ExceptionSourceIsClass, NodeSource, StrawberryException


if TYPE_CHECKING:
    from rich.console import RenderableType


class PrivateStrawberryFieldError(ExceptionSourceIsClass, StrawberryException):
    documentation_url = "https://errors.strawberry.rocks/private-strawberry-field"

    def __init__(self, field_name: str, cls: Type):
        self.cls = cls
        self.field_name = field_name

        message = (
            f"Field {field_name} on type {cls.__name__} cannot be both "
            "private and a strawberry.field"
        )

        super().__init__(message)

    @cached_property
    def attribute_source(self) -> Optional[NodeSource]:
        if self.exception_source:
            return self.exception_source.find_class_attribute(self.field_name)

        return None

    @property
    def __rich_body__(self) -> "RenderableType":
        assert self.exception_source
        assert self.attribute_source

        error_line = self.exception_source.line + self.attribute_source.line - 1

        prefix = " " * (
            self.attribute_source.column + self.exception_source.code_padding
        )
        caret = "^" * len(self.field_name)

        message = f"{prefix}[bold]{caret}[/] private field defined here"

        line_annotations = {error_line: message}

        return self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

    @property
    def __rich_header__(self) -> str:
        assert self.exception_source is not None
        assert self.attribute_source is not None

        source_file = self.exception_source.path
        relative_path = self.exception_source.path_relative_to_cwd
        error_line = self.exception_source.line + self.attribute_source.line - 1

        return (
            f"[bold red]`[underline]{self.field_name}[/]` field cannot be both "
            "private and a strawberry.field "
            f"in [white][link=file://{source_file}]{relative_path}:{error_line}"
        )

    @property
    def __rich_footer__(self) -> str:
        return (
            "To fix this error you should either make the field non private, "
            "or remove the strawberry.field annotation."
            "\n\n"
            "Read more about this error on [bold underline]"
            f"[link={self.documentation_url}]{self.documentation_url}"
        )

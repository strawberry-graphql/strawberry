from typing import TYPE_CHECKING, Optional, Type

from backports.cached_property import cached_property

from .exception import ExceptionSource, ExceptionSourceIsClass, StrawberryException


if TYPE_CHECKING:
    from rich.console import RenderableType


class MissingFieldAnnotationError(ExceptionSourceIsClass, StrawberryException):
    documentation_url = "https://errors.strawberry.rocks/missing-field-annotation"

    def __init__(self, field_name: str, cls: Type):
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f'Unable to determine the type of field "{field_name}". Either '
            f"annotate it directly, or provide a typed resolver using "
            f"@strawberry.field."
        )
        self.rich_message = (
            f"Missing annotation for field `[underline]{self.field_name}[/]`"
        )
        self.suggestion = (
            "To fix this error you can add an annotation, "
            f"like so [italic]`{self.field_name}: str`"
        )

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        exception_source = super().exception_source

        if exception_source is None:
            return None

        attribute_source = self.exception_source.find_class_attribute(self.field_name)

        if attribute_source is None:
            return None

        return ExceptionSource(
            path=exception_source.path,
            code=exception_source.code,
            start_line=exception_source.start_line,
            end_line=exception_source.end_line,
            error_line=exception_source.start_line + attribute_source.line - 1,
            error_column=attribute_source.column,
        )

    @property
    def __rich_body__(self) -> "RenderableType":
        assert self.exception_source

        error_line = self.exception_source.error_line

        prefix = " " * (
            self.exception_source.error_column + self.exception_source.code_padding
        )
        caret = "^" * len(self.field_name)

        message = f"{prefix}[bold]{caret}[/] field missing annotation"

        line_annotations = {error_line: message}

        return self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

from typing import Optional

from rich.box import SIMPLE
from rich.console import Group, RenderableType
from rich.panel import Panel

from .exception import StrawberryException


class MissingFieldAnnotationError(StrawberryException):
    documentation_url = "https://errors.strawberry.rocks/missing-field-annotation"

    def __rich__(self) -> Optional[RenderableType]:
        if not self.exception_source:
            return None

        attribute_source = self.exception_source.find_class_attribute(self.field_name)

        if attribute_source is None:
            return None

        source_file = self.exception_source.path
        relative_path = self.exception_source.path_relative_to_cwd
        error_line = self.exception_source.line + attribute_source.line - 1

        prefix = " " * (attribute_source.column + self.exception_source.code_padding)
        caret = "^" * len(self.field_name)

        message = f"{prefix}[bold]{caret}[/] field missing annotation"

        line_annotations = {error_line: message}

        code = self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

        header = (
            f"[bold red]Missing annotation for field `[underline]{self.field_name}[/]` "
            f"in [white][link=file://{source_file}]{relative_path}:{error_line}"
        )

        footer = (
            "To fix this error you can add an annotation, "
            f"like so [italic]`{self.field_name}: str`"
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
            Group(*content),
            box=SIMPLE,
        )

    def __init__(self, field_name: str, cls: type = None):
        self.cls = cls
        self.field_name = field_name

        message = (
            f'Unable to determine the type of field "{field_name}". Either '
            f"annotate it directly, or provide a typed resolver using "
            f"@strawberry.field."
        )

        super().__init__(message, cls)

from typing import Type

from .exception import ExceptionSourceIsClassAttribute, StrawberryException


class MissingFieldAnnotationError(ExceptionSourceIsClassAttribute, StrawberryException):
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
        self.annotation_message = "field missing annotation"

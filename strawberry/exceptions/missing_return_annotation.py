from typing import TYPE_CHECKING

from .exception import StrawberryException
from .exception_source.exception_source_is_resolver import ExceptionSourceIsResolver


if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver


class MissingReturnAnnotationError(ExceptionSourceIsResolver, StrawberryException):
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
            f"like so [italic]`def {self.resolver.name}(...) -> str:`"
        )
        self.annotation_message = "resolver missing annotation"

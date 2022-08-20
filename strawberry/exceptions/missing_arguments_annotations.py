from typing import TYPE_CHECKING, List

from .exception import StrawberryException
from .exception_source.exception_source_is_argument import ExceptionSourceIsArgument


if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver


class MissingArgumentsAnnotationsError(ExceptionSourceIsArgument, StrawberryException):
    """The field is missing the annotation for one or more arguments"""

    documentation_url = "https://errors.strawberry.rocks/missing-arguments-annotations"

    def __init__(self, resolver: "StrawberryResolver", arguments: List[str]):
        self.missing_arguments = arguments
        self.resolver = resolver
        self.argument_name = arguments[0]

        self.message = (
            f"Missing annotation for {self.missing_arguments_str} "
            f'in field "{self.resolver.name}", did you forget to add it?'
        )
        self.rich_message = (
            f"Missing annotation for {self.missing_arguments_str} in "
            f"`[underline]{self.resolver.name}[/]`"
        )
        self.suggestion = (
            "To fix this error you can add an annotation to the argument "
            f"like so [italic]`{self.missing_arguments[0]}: str`"
        )

        first = "first " if len(self.missing_arguments) > 1 else ""

        self.annotation_message = f"{first}argument missing annotation"

    @property
    def missing_arguments_str(self):
        arguments = self.missing_arguments

        if len(arguments) == 1:
            return f'argument "{arguments[0]}"'

        head = ", ".join(arguments[:-1])
        return f'arguments "{head}" and "{arguments[-1]}"'

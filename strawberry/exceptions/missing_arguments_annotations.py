from typing import TYPE_CHECKING, List

from .exception import StrawberryException
from .exception_source import ExceptionSourceIsArgument


if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver


class MissingArgumentsAnnotationsError(ExceptionSourceIsArgument, StrawberryException):
    """The field is missing the annotation for one or more arguments"""

    def __init__(self, resolver: "StrawberryResolver", arguments: List[str]):
        self.missing_arguments = arguments
        self.function = resolver.wrapped_func
        self.argument_name = arguments[0]

        self.message = (
            f"Missing annotation for {self.missing_arguments_str} "
            f'in field "{resolver.name}", did you forget to add it?'
        )
        self.rich_message = (
            f"Missing annotation for {self.missing_arguments_str} in "
            f"`[underline]{resolver.name}[/]`"
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

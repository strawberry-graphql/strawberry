from typing import TYPE_CHECKING

from typing_extensions import Literal

from .exception import StrawberryException
from .exception_source import ExceptionSourceIsArgument


if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver


class InvalidArgumentTypeError(ExceptionSourceIsArgument, StrawberryException):
    def __init__(
        self,
        resolver: "StrawberryResolver",
        argument_name: str,
        argument_type: Literal["union", "interface"],
    ):
        self.function = resolver.wrapped_func
        self.argument_name = argument_name

        self.message = (
            f'Argument "{argument_name}" on field "{resolver.name}" cannot be of type '
            f'"{argument_type}"'
        )
        self.rich_message = self.message

        if argument_type == "union":
            self.suggestion = "Unions are not supported as arguments in GraphQL."
        elif argument_type == "interface":
            self.suggestion = "Interfaces are not supported as arguments in GraphQL."
        else:
            self.suggestion = f"{argument_name} is not supported as an argument."

        self.annotation_message = (
            f'Argument "{argument_name}" cannot be of type "{argument_type}"'
        )

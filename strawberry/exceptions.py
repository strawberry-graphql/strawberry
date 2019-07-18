# TODO: add links to docs

from typing import List, Set

from graphql import GraphQLObjectType


class NotAnEnum(Exception):
    def __init__(self):
        message = "strawberry.enum can only be used with subclasses of Enum"

        super().__init__(message)


class MissingReturnAnnotationError(Exception):
    """The field is missing the return annotation"""

    def __init__(self, field_name: str):
        message = (
            f'Return annotation missing for field "{field_name}", '
            "did you forget to add it?"
        )

        super().__init__(message)


class MissingArgumentsAnnotationsError(Exception):
    """The field is missing the annotation for one or more arguments"""

    def __init__(self, field_name: str, arguments: Set[str]):
        arguments_list: List[str] = sorted(list(arguments))

        if len(arguments_list) == 1:
            argument = f'argument "{arguments_list[0]}"'
        else:
            head = ", ".join(arguments_list[:-1])
            argument = f'arguments "{head}" and "{arguments_list[-1]}"'

        message = (
            f"Missing annotation for {argument} "
            f'in field "{field_name}", did you forget to add it?'
        )

        super().__init__(message)


class WrongReturnTypeForUnion(Exception):
    """The Union type cannot be resolved because it's not a field"""

    def __init__(self, field_name: str, result_type: str):
        message = (
            f'The type "{result_type}" cannot be resolved for the field "{field_name}" '
            ", are you using a strawberry.field?"
        )

        super().__init__(message)


class UnallowedReturnTypeForUnion(Exception):
    """The return type is not in the list of Union types"""

    def __init__(
        self, field_name: str, result_type: str, allowed_types: Set[GraphQLObjectType]
    ):
        formatted_allowed_types = [type_.name for type_ in allowed_types]

        message = (
            f'The type "{result_type}" of the field "{field_name}" '
            f'is not in the list of the types of the union: "{formatted_allowed_types}"'
        )

        super().__init__(message)

# TODO: add links to docs

from typing import List, Set, Union

from graphql import GraphQLObjectType

from strawberry.type import StrawberryType


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
        formatted_allowed_types = list(sorted(type_.name for type_ in allowed_types))

        message = (
            f'The type "{result_type}" of the field "{field_name}" '
            f'is not in the list of the types of the union: "{formatted_allowed_types}"'
        )

        super().__init__(message)


class InvalidUnionType(Exception):
    """The union is constructed with an invalid type"""

    pass


class MissingTypesForGenericError(Exception):
    """Raised when a generic types was used without passing any type."""

    def __init__(self, annotation: Union[StrawberryType, type]):
        message = (
            f'The type "{repr(annotation)}" is generic, but no type has been passed'
        )

        super().__init__(message)


class UnsupportedTypeError(Exception):
    def __init__(self, annotation):
        message = f"{annotation} conversion is not supported"

        super().__init__(message)


class MissingFieldAnnotationError(Exception):
    def __init__(self, field_name: str):
        message = (
            f'Unable to determine the type of field "{field_name}". Either '
            f"annotate it directly, or provide a typed resolver using "
            f"@strawberry.field."
        )

        super().__init__(message)


class PrivateStrawberryFieldError(Exception):
    def __init__(self, field_name: str, type_name: str):
        message = (
            f"Field {field_name} on type {type_name} cannot be both "
            "private and a strawberry.field"
        )

        super().__init__(message)


class MultipleStrawberryArgumentsError(Exception):
    def __init__(self, argument_name: str):
        message = (
            f"Annotation for argument `{argument_name}` cannot have multiple "
            f"`strawberry.argument`s"
        )

        super().__init__(message)


class ScalarAlreadyRegisteredError(Exception):
    def __init__(self, scalar_name: str):
        message = f"Scalar `{scalar_name}` has already been registered"

        super().__init__(message)


class WrongNumberOfResultsReturned(Exception):
    def __init__(self, expected: int, received: int):
        message = (
            "Received wrong number of results in dataloader, "
            f"expected: {expected}, received: {received}"
        )

        super().__init__(message)


class FieldWithResolverAndDefaultValueError(Exception):
    def __init__(self, field_name: str, type_name: str):
        message = (
            f'Field "{field_name}" on type "{type_name}" cannot define a default '
            "value and a resolver."
        )

        super().__init__(message)


class FieldWithResolverAndDefaultFactoryError(Exception):
    def __init__(self, field_name: str, type_name: str):
        message = (
            f'Field "{field_name}" on type "{type_name}" cannot define a '
            "default_factory and a resolver."
        )

        super().__init__(message)


class MissingQueryError(Exception):
    def __init__(self):
        message = 'Request data is missing a "query" value'

        super().__init__(message)

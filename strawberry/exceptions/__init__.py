from __future__ import annotations

import sys
from enum import Enum
from typing import Set, Union

from graphql import GraphQLInputObjectType, GraphQLObjectType

from strawberry.type import StrawberryType

from .exception import StrawberryException
from .invalid_argument_type import InvalidArgumentTypeError
from .invalid_union_type import InvalidTypeForUnionMergeError, InvalidUnionTypeError
from .missing_arguments_annotations import MissingArgumentsAnnotationsError
from .missing_field_annotation import MissingFieldAnnotationError
from .missing_return_annotation import MissingReturnAnnotationError
from .private_strawberry_field import PrivateStrawberryFieldError


class ObjectIsNotAnEnumError(StrawberryException):
    def __init__(self, obj: object):
        message = (
            "strawberry.enum can only be used with subclasses of Enum. "
            f"Provided object {obj} is not an enum."
        )

        super().__init__(message)


class ObjectIsNotClassError(StrawberryException):
    class MethodType(Enum):
        INPUT = "input"
        INTERFACE = "interface"
        TYPE = "type"

    def __init__(self, obj: object, method_type: MethodType):
        message = (
            f"strawberry.{method_type.value} can only be used with class types. "
            f"Provided object {obj} is not a type."
        )

        super().__init__(message)

    @classmethod
    def input(cls, obj: object) -> ObjectIsNotClassError:
        return cls(obj, cls.MethodType.INPUT)

    @classmethod
    def interface(cls, obj: object) -> ObjectIsNotClassError:
        return cls(obj, cls.MethodType.INTERFACE)

    @classmethod
    def type(cls, obj: object) -> ObjectIsNotClassError:
        return cls(obj, cls.MethodType.TYPE)


class WrongReturnTypeForUnion(StrawberryException):
    """The Union type cannot be resolved because it's not a field"""

    def __init__(self, field_name: str, result_type: str):
        message = (
            f'The type "{result_type}" cannot be resolved for the field "{field_name}" '
            ", are you using a strawberry.field?"
        )

        super().__init__(message)


class UnallowedReturnTypeForUnion(StrawberryException):
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


class InvalidTypeInputForUnion(StrawberryException):
    def __init__(self, annotation: GraphQLInputObjectType):
        message = f"Union for {annotation} is not supported because it is an Input type"
        super().__init__(message)


class MissingTypesForGenericError(StrawberryException):
    """Raised when a generic types was used without passing any type."""

    def __init__(self, annotation: Union[StrawberryType, type]):
        message = (
            f'The type "{repr(annotation)}" is generic, but no type has been passed'
        )

        super().__init__(message)


class UnsupportedTypeError(StrawberryException):
    def __init__(self, annotation):
        message = f"{annotation} conversion is not supported"

        super().__init__(message)


class UnresolvedFieldTypeError(StrawberryException):
    def __init__(self, field_name: str):
        message = (
            f"Could not resolve the type of '{field_name}'. Check that the class is "
            "accessible from the global module scope."
        )
        super().__init__(message)


class MultipleStrawberryArgumentsError(StrawberryException):
    def __init__(self, argument_name: str):
        message = (
            f"Annotation for argument `{argument_name}` cannot have multiple "
            f"`strawberry.argument`s"
        )

        super().__init__(message)


class ScalarAlreadyRegisteredError(StrawberryException):
    def __init__(self, scalar_name: str):
        message = f"Scalar `{scalar_name}` has already been registered"

        super().__init__(message)


class WrongNumberOfResultsReturned(StrawberryException):
    def __init__(self, expected: int, received: int):
        message = (
            "Received wrong number of results in dataloader, "
            f"expected: {expected}, received: {received}"
        )

        super().__init__(message)


class FieldWithResolverAndDefaultValueError(StrawberryException):
    def __init__(self, field_name: str, type_name: str):
        message = (
            f'Field "{field_name}" on type "{type_name}" cannot define a default '
            "value and a resolver."
        )

        super().__init__(message)


class FieldWithResolverAndDefaultFactoryError(StrawberryException):
    def __init__(self, field_name: str, type_name: str):
        message = (
            f'Field "{field_name}" on type "{type_name}" cannot define a '
            "default_factory and a resolver."
        )

        super().__init__(message)


class MissingQueryError(StrawberryException):
    def __init__(self):
        message = 'Request data is missing a "query" value'

        super().__init__(message)


class InvalidDefaultFactoryError(StrawberryException):
    def __init__(self):
        message = "`default_factory` must be a callable that requires no arguments"

        super().__init__(message)


class InvalidCustomContext(StrawberryException):
    """Raised when a custom context object is of the wrong python type"""

    def __init__(self):
        message = (
            "The custom context must be either a class "
            "that inherits from BaseContext or a dictionary"
        )
        super().__init__(message)


def exception_handler(exception_type, exception, traceback):
    import rich

    if isinstance(exception, StrawberryException):
        rich.print(exception)
    else:
        print("%s: %s" % (exception_type.__name__, exception))


sys.excepthook = exception_handler


__all__ = [
    "StrawberryException",
    "MissingArgumentsAnnotationsError",
    "MissingReturnAnnotationError",
    "MissingReturnTypeError",
    "WrongReturnTypeForUnion",
    "UnallowedReturnTypeForUnion",
    "InvalidUnionTypeError",
    "InvalidTypeForUnionMergeError",
    "MissingTypesForGenericError",
    "UnsupportedTypeError",
    "UnresolvedFieldTypeError",
    "PrivateStrawberryFieldError",
    "MultipleStrawberryArgumentsError",
    "ScalarAlreadyRegisteredError",
    "WrongNumberOfResultsReturned",
    "FieldWithResolverAndDefaultValueError",
    "FieldWithResolverAndDefaultFactoryError",
    "MissingQueryError",
    "InvalidArgumentTypeError",
    "InvalidDefaultFactoryError",
    "InvalidCustomContext",
    "MissingFieldAnnotationError",
]

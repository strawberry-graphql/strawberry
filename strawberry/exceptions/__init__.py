from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional, Set, Union

from graphql import GraphQLError

from .conflicting_arguments import ConflictingArgumentsError
from .duplicated_type_name import DuplicatedTypeName
from .exception import StrawberryException, UnableToFindExceptionSource
from .handler import setup_exception_handler
from .invalid_argument_type import InvalidArgumentTypeError
from .invalid_union_type import InvalidTypeForUnionMergeError, InvalidUnionTypeError
from .missing_arguments_annotations import MissingArgumentsAnnotationsError
from .missing_dependencies import MissingOptionalDependenciesError
from .missing_field_annotation import MissingFieldAnnotationError
from .missing_return_annotation import MissingReturnAnnotationError
from .not_a_strawberry_enum import NotAStrawberryEnumError
from .object_is_not_a_class import ObjectIsNotClassError
from .object_is_not_an_enum import ObjectIsNotAnEnumError
from .private_strawberry_field import PrivateStrawberryFieldError
from .scalar_already_registered import ScalarAlreadyRegisteredError
from .unresolved_field_type import UnresolvedFieldTypeError

if TYPE_CHECKING:
    from graphql import GraphQLInputObjectType, GraphQLObjectType

    from strawberry.type import StrawberryType

    from .exception_source import ExceptionSource

setup_exception_handler()


# TODO: this doesn't seem to be tested
class WrongReturnTypeForUnion(Exception):
    """The Union type cannot be resolved because it's not a field"""

    def __init__(self, field_name: str, result_type: str) -> None:
        message = (
            f'The type "{result_type}" cannot be resolved for the field "{field_name}" '
            ", are you using a strawberry.field?"
        )

        super().__init__(message)


class UnallowedReturnTypeForUnion(Exception):
    """The return type is not in the list of Union types"""

    def __init__(
        self, field_name: str, result_type: str, allowed_types: Set[GraphQLObjectType]
    ) -> None:
        formatted_allowed_types = list(sorted(type_.name for type_ in allowed_types))

        message = (
            f'The type "{result_type}" of the field "{field_name}" '
            f'is not in the list of the types of the union: "{formatted_allowed_types}"'
        )

        super().__init__(message)


# TODO: this doesn't seem to be tested
class InvalidTypeInputForUnion(Exception):
    def __init__(self, annotation: GraphQLInputObjectType) -> None:
        message = f"Union for {annotation} is not supported because it is an Input type"
        super().__init__(message)


# TODO: this doesn't seem to be tested
class MissingTypesForGenericError(Exception):
    """Raised when a generic types was used without passing any type."""

    def __init__(self, annotation: Union[StrawberryType, type]) -> None:
        message = f'The type "{annotation!r}" is generic, but no type has been passed'

        super().__init__(message)


class UnsupportedTypeError(StrawberryException):
    def __init__(self, annotation: Union[StrawberryType, type]) -> None:
        message = f"{annotation} conversion is not supported"

        super().__init__(message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        return None


class MultipleStrawberryArgumentsError(Exception):
    def __init__(self, argument_name: str) -> None:
        message = (
            f"Annotation for argument `{argument_name}` cannot have multiple "
            f"`strawberry.argument`s"
        )

        super().__init__(message)


class WrongNumberOfResultsReturned(Exception):
    def __init__(self, expected: int, received: int) -> None:
        message = (
            "Received wrong number of results in dataloader, "
            f"expected: {expected}, received: {received}"
        )

        super().__init__(message)


class FieldWithResolverAndDefaultValueError(Exception):
    def __init__(self, field_name: str, type_name: str) -> None:
        message = (
            f'Field "{field_name}" on type "{type_name}" cannot define a default '
            "value and a resolver."
        )

        super().__init__(message)


class FieldWithResolverAndDefaultFactoryError(Exception):
    def __init__(self, field_name: str, type_name: str) -> None:
        message = (
            f'Field "{field_name}" on type "{type_name}" cannot define a '
            "default_factory and a resolver."
        )

        super().__init__(message)


class MissingQueryError(Exception):
    def __init__(self) -> None:
        message = 'Request data is missing a "query" value'

        super().__init__(message)


class InvalidDefaultFactoryError(Exception):
    def __init__(self) -> None:
        message = "`default_factory` must be a callable that requires no arguments"

        super().__init__(message)


class InvalidCustomContext(Exception):
    """Raised when a custom context object is of the wrong python type"""

    def __init__(self) -> None:
        message = (
            "The custom context must be either a class "
            "that inherits from BaseContext or a dictionary"
        )
        super().__init__(message)


class StrawberryGraphQLError(GraphQLError):
    """Use it when you want to override the graphql.GraphQLError in custom extensions"""


__all__ = [
    "StrawberryException",
    "UnableToFindExceptionSource",
    "MissingArgumentsAnnotationsError",
    "MissingReturnAnnotationError",
    "WrongReturnTypeForUnion",
    "UnallowedReturnTypeForUnion",
    "ObjectIsNotAnEnumError",
    "ObjectIsNotClassError",
    "InvalidUnionTypeError",
    "InvalidTypeForUnionMergeError",
    "MissingTypesForGenericError",
    "UnsupportedTypeError",
    "UnresolvedFieldTypeError",
    "PrivateStrawberryFieldError",
    "MultipleStrawberryArgumentsError",
    "NotAStrawberryEnumError",
    "ScalarAlreadyRegisteredError",
    "WrongNumberOfResultsReturned",
    "FieldWithResolverAndDefaultValueError",
    "FieldWithResolverAndDefaultFactoryError",
    "ConflictingArgumentsError",
    "MissingQueryError",
    "InvalidArgumentTypeError",
    "InvalidDefaultFactoryError",
    "InvalidCustomContext",
    "MissingFieldAnnotationError",
    "DuplicatedTypeName",
    "StrawberryGraphQLError",
    "MissingOptionalDependenciesError",
]

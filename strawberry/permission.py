from __future__ import annotations

import abc
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    List,
    Optional,
    Type,
    Union,
    cast,
)

from graphql import GraphQLError

from strawberry.exceptions import StrawberryGraphQLError
from strawberry.extensions import FieldExtension
from strawberry.schema_directive import Location, StrawberrySchemaDirective
from strawberry.utils.await_maybe import await_maybe

if TYPE_CHECKING:
    from strawberry.field import StrawberryField
    from strawberry.types import Info


class BasePermission(abc.ABC):
    """
    Base class for creating permissions
    """

    message: Optional[str] = None

    error_extensions: Optional[dict[str, str]] = None

    error_class: Type[GraphQLError] = StrawberryGraphQLError

    _schema_directive: Optional[StrawberrySchemaDirective] = None

    @abc.abstractmethod
    def has_permission(
        self, source: Any, info: Info, **kwargs
    ) -> Union[bool, Awaitable[bool]]:
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )

    def raise_error(self) -> None:
        """
        Default error raising for permissions. This can be overridden to customize the behavior.
        """

        # Instantiate error class
        error = self.error_class(self.message)

        if self.error_extensions:
            # If no custom error class is used, use the standard GraphQLError so we can add the extensions
            if not error:
                error = GraphQLError(self.message)
            # Add our extensions to the error
            error.extensions.update(self.error_extensions)

        # If none of the new attributes were used, fall back to prevent breaking changes
        if not error:
            raise PermissionError(self.message)

        raise error

    @property
    def schema_directive(self) -> Optional[StrawberrySchemaDirective]:
        if not self._schema_directive:
            self._schema_directive = StrawberrySchemaDirective(
                self.__class__.__name__,
                self.__class__.__name__,
                [Location.FIELD_DEFINITION],
                [],
            )
        return self._schema_directive


class PermissionExtension(FieldExtension):
    def __init__(self, permissions: List[BasePermission]):
        self.permissions = permissions

    def apply(self, field: StrawberryField) -> None:  # nocov
        """Applies all of the permission directives to the schema"""
        for permission in self.permissions:
            if permission.schema_directive:
                cast(List, field.directives).append(permission.schema_directive)

    def resolve(
        self, next: Callable[..., Any], source: Any, info: Info, **kwargs
    ) -> Any:
        """
        Checks if the permission should be accepted and
        raises an exception if not
        """
        for permission in self.permissions:
            if not permission.has_permission(source, info, **kwargs):
                permission.raise_error()

    async def resolve_async(
        self, next: Callable[..., Any], source: Any, info: Info, **kwargs
    ) -> Any:
        for permission in self.permissions:
            has_permission: bool

            has_permission = await await_maybe(
                permission.has_permission(source, info, **kwargs)
            )

            if not has_permission:
                permission.raise_error()

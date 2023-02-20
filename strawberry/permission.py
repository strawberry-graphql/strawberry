from __future__ import annotations

import abc
from inspect import iscoroutinefunction
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

from strawberry.exceptions import StrawberryGraphQLError
from strawberry.extensions import FieldExtension
from strawberry.schema_directive import Location, StrawberrySchemaDirective
from strawberry.utils.await_maybe import await_maybe
from strawberry.utils.cached_property import cached_property

if TYPE_CHECKING:
    from graphql import GraphQLError, GraphQLErrorExtensions

    from strawberry.field import StrawberryField
    from strawberry.types import Info


class BasePermission(abc.ABC):
    """
    Base class for creating permissions
    """

    message: Optional[str] = None

    error_extensions: Optional[GraphQLErrorExtensions] = None

    error_class: Type[GraphQLError] = StrawberryGraphQLError

    _schema_directive: Optional[StrawberrySchemaDirective] = None

    @abc.abstractmethod
    def has_permission(
        self, source: Any, info: Info, **kwargs
    ) -> Union[bool, Awaitable[bool]]:
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )

    def get_error(self) -> GraphQLError:
        """
        Default error raising for permissions.
        This can be overridden to customize the behavior.
        """

        # Instantiate error class
        error = self.error_class(self.message or "")

        if self.error_extensions:
            # Add our extensions to the error
            if not error.extensions:
                error.extensions = dict()
            error.extensions.update(self.error_extensions)

        return error

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
                raise permission.get_error()
        return next(source, info, **kwargs)

    async def resolve_async(
        self, next: Callable[..., Any], source: Any, info: Info, **kwargs
    ) -> Any:
        for permission in self.permissions:
            has_permission: bool

            has_permission = await await_maybe(
                permission.has_permission(source, info, **kwargs)
            )

            if not has_permission:
                raise permission.get_error()
        return await next(source, info, **kwargs)

    @cached_property
    def supports_sync(self) -> bool:
        """The Permission extension always supports async checking using await_maybe,
        but only supports sync checking if there are no async permissions"""
        async_permissions = [
            True
            for permission in self.permissions
            if iscoroutinefunction(permission.has_permission)
        ]
        return len(async_permissions) == 0

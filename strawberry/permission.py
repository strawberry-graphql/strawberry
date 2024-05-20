from __future__ import annotations

import abc
import inspect
from functools import cached_property
from inspect import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Dict,
    List,
    Optional,
    Type,
    Union,
)

from strawberry.exceptions import StrawberryGraphQLError
from strawberry.exceptions.permission_fail_silently_requires_optional import (
    PermissionFailSilentlyRequiresOptionalError,
)
from strawberry.extensions import FieldExtension
from strawberry.schema_directive import Location, StrawberrySchemaDirective
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.utils.await_maybe import await_maybe

if TYPE_CHECKING:
    from graphql import GraphQLError, GraphQLErrorExtensions

    from strawberry.extensions.field_extension import (
        AsyncExtensionResolver,
        SyncExtensionResolver,
    )
    from strawberry.field import StrawberryField
    from strawberry.types import Info


class BasePermission(abc.ABC):
    """
    Base class for creating permissions
    """

    message: Optional[str] = None

    error_extensions: Optional[GraphQLErrorExtensions] = None

    error_class: Type[GraphQLError] = StrawberryGraphQLError

    _schema_directive: Optional[object] = None

    @abc.abstractmethod
    def has_permission(
        self, source: Any, info: Info, **kwargs: Any
    ) -> Union[bool, Awaitable[bool]]:
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )

    def on_unauthorized(self) -> None:
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

        raise error

    @property
    def schema_directive(self) -> object:
        if not self._schema_directive:

            class AutoDirective:
                __strawberry_directive__ = StrawberrySchemaDirective(
                    self.__class__.__name__,
                    self.__class__.__name__,
                    [Location.FIELD_DEFINITION],
                    [],
                )

            self._schema_directive = AutoDirective()

        return self._schema_directive


class PermissionExtension(FieldExtension):
    """
    Handles permissions for a field
    Instantiate this as a field extension with all of the permissions you want to apply

    fail_silently: bool = False will return None or [] if the permission fails
    instead of raising an exception. This is only valid for optional or list fields.

    NOTE:
    Currently, this is automatically added to the field, when using
    field.permission_classes
    This is deprecated behavior, please manually add the extension to field.extensions
    """

    def __init__(
        self,
        permissions: List[BasePermission],
        use_directives: bool = True,
        fail_silently: bool = False,
    ) -> None:
        self.permissions = permissions
        self.fail_silently = fail_silently
        self.return_empty_list = False
        self.use_directives = use_directives

    def apply(self, field: StrawberryField) -> None:
        """
        Applies all of the permission directives to the schema
        and sets up silent permissions
        """
        if self.use_directives:
            field.directives.extend(
                p.schema_directive for p in self.permissions if p.schema_directive
            )
        # We can only fail silently if the field is optional or a list
        if self.fail_silently:
            if isinstance(field.type, StrawberryOptional):
                if isinstance(field.type.of_type, StrawberryList):
                    self.return_empty_list = True
            elif isinstance(field.type, StrawberryList):
                self.return_empty_list = True
            else:
                errror = PermissionFailSilentlyRequiresOptionalError(field)
                raise errror

    def _on_unauthorized(self, permission: BasePermission) -> Any:
        if self.fail_silently:
            return [] if self.return_empty_list else None
        return permission.on_unauthorized()

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: Dict[str, Any],
    ) -> Any:
        """
        Checks if the permission should be accepted and
        raises an exception if not
        """
        for permission in self.permissions:
            if not permission.has_permission(source, info, **kwargs):
                return self._on_unauthorized(permission)
        return next_(source, info, **kwargs)

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: Dict[str, Any],
    ) -> Any:
        for permission in self.permissions:
            has_permission = await await_maybe(
                permission.has_permission(source, info, **kwargs)
            )

            if not has_permission:
                return self._on_unauthorized(permission)
        next = next_(source, info, **kwargs)
        if inspect.isasyncgen(next):
            return next
        return await next

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

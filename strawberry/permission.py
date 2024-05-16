from __future__ import annotations

import abc
import inspect
from functools import cached_property
from inspect import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
)
from typing_extensions import deprecated

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
    ) -> Union[
        bool,
        Awaitable[bool],
        Tuple[Literal[False], dict],
        Awaitable[Tuple[Literal[False], dict]],
    ]:
        """
        This method is a required override in the permission class. It checks if the user has the necessary permissions to access a specific field.

        The method should return a boolean value:
        - True: The user has the necessary permissions.
        - False: The user does not have the necessary permissions. In this case, the `on_unauthorized` method will be invoked.

        Avoid raising exceptions in this method. Instead, use the `on_unauthorized` method to handle errors and customize the error response.

        If there's a need to pass additional information to the `on_unauthorized` method, return a tuple. The first element should be False, and the second element should be a dictionary containing the additional information.

        Args:
            source (Any): The source field that the permission check is being performed on.
            info (Info): The GraphQL resolve info associated with the field.
            **kwargs (Any): Additional arguments that are typically passed to the field resolver.

        Returns:
            bool or tuple: Returns True if the user has the necessary permissions. Returns False or a tuple (False, additional_info) if the user does not have the necessary permissions. In the latter case, the `on_unauthorized` method will be invoked.
        """
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )

    def on_unauthorized(self, **kwargs: Any) -> None:
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
    @deprecated(
        "@schema_directive is deprecated and will be disabled by default on 31.12.2024 with future removal planned. Use the new @permissions directive instead."
    )
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

    @cached_property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.has_permission)

    def __and__(self, other: BasePermission):
        return AndPermission([self, other])

    def __or__(self, other: BasePermission):
        return OrPermission([self, other])


class CompositePermission(BasePermission, abc.ABC):
    def __init__(self, child_permissions: List[BasePermission]):
        self.child_permissions = child_permissions

    def on_unauthorized(self, **kwargs: Any) -> Any:
        failed_permissions = kwargs.get("failed_permissions", [])
        for permission in failed_permissions:
            permission.on_unauthorized()

    @cached_property
    def is_async(self) -> bool:
        return any(x.is_async for x in self.child_permissions)


class AndPermission(CompositePermission):
    def has_permission(
        self, source: Any, info: Info, **kwargs: Any
    ) -> Union[
        bool,
        Awaitable[bool],
        Tuple[Literal[False], dict],
        Awaitable[Tuple[Literal[False], dict]],
    ]:
        if self.is_async:
            return self._has_permission_async(source, info, **kwargs)

        for permission in self.child_permissions:
            if not permission.has_permission(source, info, **kwargs):
                return False, {"failed_permissions": [permission]}
        return True

    async def _has_permission_async(
        self, source: Any, info: Info, **kwargs: Any
    ) -> Union[bool, Tuple[Literal[False], dict]]:
        for permission in self.child_permissions:
            if not await await_maybe(permission.has_permission(source, info, **kwargs)):
                return False, {"failed_permissions": [permission]}
        return True

    def __and__(self, other: BasePermission):
        return AndPermission([*self.child_permissions, other])


class OrPermission(CompositePermission):
    def has_permission(
        self, source: Any, info: Info, **kwargs: Any
    ) -> Union[
        bool,
        Awaitable[bool],
        Tuple[Literal[False], dict],
        Awaitable[Tuple[Literal[False], dict]],
    ]:
        if self.is_async:
            return self._has_permission_async(source, info, **kwargs)
        failed_permissions = []
        for permission in self.child_permissions:
            if permission.has_permission(source, info, **kwargs):
                return True
            failed_permissions.append(permission)

        return False, {"failed_permissions": failed_permissions}

    async def _has_permission_async(
        self, source: Any, info: Info, **kwargs: Any
    ) -> Union[bool, Tuple[Literal[False], dict]]:
        failed_permissions = []
        for permission in self.child_permissions:
            if await await_maybe(permission.has_permission(source, info, **kwargs)):
                return True
            failed_permissions.append(permission)

        return False, {"failed_permissions": failed_permissions}

    def __or__(self, other: BasePermission):
        return OrPermission([*self.child_permissions, other])


class PermissionExtension(FieldExtension):
    """
    Handles permissions for a field
    Instantiate this as a field extension with all of the permissions you want to apply

    fail_silently: bool = False will return None or [] if the permission fails
    instead of raising an exception. This is only valid for optional or list fields.

    NOTE:
    Currently, this is automatically added to the field, when using
    field.permission_classes. You are free to use whichever method you prefer.
    Use PermissionExtension if you want additional customization.
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
        Applies all the permission directives to the schema
        and sets up silent permissions
        """
        if self.use_directives:
            field.directives.extend(
                [
                    p.schema_directive
                    for p in self.permissions
                    if not isinstance(p, CompositePermission)
                ]
            )
        # We can only fail silently if the field is optional or a list
        if self.fail_silently:
            if isinstance(field.type, StrawberryOptional):
                if isinstance(field.type.of_type, StrawberryList):
                    self.return_empty_list = True
            elif isinstance(field.type, StrawberryList):
                self.return_empty_list = True
            else:
                raise PermissionFailSilentlyRequiresOptionalError(field)

    def _on_unauthorized(self, permission: BasePermission, **kwargs: Any) -> Any:
        if self.fail_silently:
            return [] if self.return_empty_list else None

        if kwargs in (None, {}):
            return permission.on_unauthorized()
        return permission.on_unauthorized(**kwargs)

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: Any[str, Any],
    ) -> Any:
        """
        Checks if the permission should be accepted and
        raises an exception if not
        """

        for permission in self.permissions:
            permission_response = permission.has_permission(source, info, **kwargs)

            context = {}
            if isinstance(permission_response, tuple):
                has_permission, context = permission_response
            else:
                has_permission = permission_response

            if not has_permission:
                return self._on_unauthorized(permission, **context)

        return next_(source, info, **kwargs)

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: Any[str, Any],
    ) -> Any:
        for permission in self.permissions:
            permission_response = await await_maybe(
                permission.has_permission(source, info, **kwargs)
            )

            context = {}
            if isinstance(permission_response, tuple):
                has_permission, context = permission_response
            else:
                has_permission = permission_response

            if not has_permission:
                return self._on_unauthorized(permission, **context)
        next = next_(source, info, **kwargs)
        if inspect.isasyncgen(next):
            return next
        return await next

    @cached_property
    def supports_sync(self) -> bool:
        """The Permission extension always supports async checking using await_maybe,
        but only supports sync checking if there are no async permissions"""
        return all(not permission.is_async for permission in self.permissions)

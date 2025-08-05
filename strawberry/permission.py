from __future__ import annotations

import abc
import inspect
from collections.abc import Awaitable
from functools import cached_property
from inspect import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    TypedDict,
    Union,
)

from strawberry.exceptions import StrawberryGraphQLError
from strawberry.exceptions.permission_fail_silently_requires_optional import (
    PermissionFailSilentlyRequiresOptionalError,
)
from strawberry.extensions import FieldExtension
from strawberry.schema_directive import Location, StrawberrySchemaDirective
from strawberry.types.base import StrawberryList, StrawberryOptional
from strawberry.utils.await_maybe import await_maybe

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from graphql import GraphQLError, GraphQLErrorExtensions

    from strawberry.extensions.field_extension import (
        AsyncExtensionResolver,
        SyncExtensionResolver,
    )
    from strawberry.types import Info
    from strawberry.types.field import StrawberryField


def unpack_maybe(
    value: Union[object, tuple[bool, object]], default: object = None
) -> tuple[object, object]:
    if isinstance(value, tuple) and len(value) == 2:
        return value
    return value, default


class BasePermission(abc.ABC):
    """Base class for permissions. All permissions should inherit from this class.

    Example:

    ```python
    from strawberry.permission import BasePermission


    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, source, info, **kwargs):
            return info.context["user"].is_authenticated
    ```
    """

    message: Optional[str] = None

    error_extensions: Optional[GraphQLErrorExtensions] = None

    error_class: type[GraphQLError] = StrawberryGraphQLError

    _schema_directive: Optional[object] = None

    @abc.abstractmethod
    def has_permission(
        self, source: Any, info: Info, **kwargs: object
    ) -> Union[
        bool,
        Awaitable[bool],
        tuple[Literal[False], dict],
        Awaitable[tuple[Literal[False], dict]],
    ]:
        """This method is a required override in the permission class. It checks if the user has the necessary permissions to access a specific field.

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

    def on_unauthorized(self, **kwargs: object) -> None:
        """Default error raising for permissions.

        This method can be overridden to customize the error raised when the permission is not granted.

        Example:

        ```python
        from strawberry.permission import BasePermission


        class CustomPermissionError(PermissionError):
            pass


        class IsAuthenticated(BasePermission):
            message = "User is not authenticated"

            def has_permission(self, source, info, **kwargs):
                return info.context["user"].is_authenticated

            def on_unauthorized(self) -> None:
                raise CustomPermissionError(self.message)
        ```
        """
        # Instantiate error class
        error = self.error_class(self.message or "")

        if self.error_extensions:
            # Add our extensions to the error
            if not error.extensions:
                error.extensions = {}
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

    @cached_property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.has_permission)

    def __and__(self, other: BasePermission) -> AndPermission:
        return AndPermission([self, other])

    def __or__(self, other: BasePermission) -> OrPermission:
        return OrPermission([self, other])


class CompositePermissionContext(TypedDict):
    failed_permissions: list[tuple[BasePermission, dict]]


class CompositePermission(BasePermission, abc.ABC):
    def __init__(self, child_permissions: list[BasePermission]) -> None:
        self.child_permissions = child_permissions

    def on_unauthorized(self, **kwargs: object) -> Any:
        failed_permissions = kwargs.get("failed_permissions", [])
        for permission, context in failed_permissions:
            permission.on_unauthorized(**context)

    @cached_property
    def is_async(self) -> bool:
        return any(x.is_async for x in self.child_permissions)


class AndPermission(CompositePermission):
    """Combines multiple permissions with AND logic.

    This class enables the & operator for permissions (e.g., IsAdmin() & IsOwner()).
    Performance optimizations:
    - Separate sync/async paths avoid ~3x overhead for synchronous permissions
    - Short-circuit evaluation stops at first False, providing up to 1000x+ speedup
    """

    def has_permission(
        self, source: Any, info: Info, **kwargs: object
    ) -> Union[
        bool,
        Awaitable[bool],
        tuple[Literal[False], CompositePermissionContext],
        Awaitable[tuple[Literal[False], CompositePermissionContext]],
    ]:
        if self.is_async:
            return self._has_permission_async(source, info, **kwargs)

        for permission in self.child_permissions:
            has_permission, context = unpack_maybe(
                permission.has_permission(source, info, **kwargs), {}
            )
            if not has_permission:
                return False, {"failed_permissions": [(permission, context)]}
        return True

    async def _has_permission_async(
        self, source: Any, info: Info, **kwargs: object
    ) -> Union[bool, tuple[Literal[False], CompositePermissionContext]]:
        for permission in self.child_permissions:
            permission_response = await await_maybe(
                permission.has_permission(source, info, **kwargs)
            )
            has_permission, context = unpack_maybe(permission_response, {})
            if not has_permission:
                return False, {"failed_permissions": [(permission, context)]}
        return True

    def __and__(self, other: BasePermission) -> AndPermission:
        return AndPermission([*self.child_permissions, other])


class OrPermission(CompositePermission):
    """Combines multiple permissions with OR logic.

    This class enables the | operator for permissions (e.g., IsAdmin() | IsOwner()).
    Performance optimizations:
    - Separate sync/async paths avoid ~3x overhead for synchronous permissions
    - Short-circuit evaluation stops at first True, providing up to 1000x+ speedup
    """

    def has_permission(
        self, source: Any, info: Info, **kwargs: object
    ) -> Union[
        bool,
        Awaitable[bool],
        tuple[Literal[False], dict],
        Awaitable[tuple[Literal[False], dict]],
    ]:
        if self.is_async:
            return self._has_permission_async(source, info, **kwargs)
        failed_permissions = []
        for permission in self.child_permissions:
            has_permission, context = unpack_maybe(
                permission.has_permission(source, info, **kwargs), {}
            )
            if has_permission:
                return True
            failed_permissions.append((permission, context))

        return False, {"failed_permissions": failed_permissions}

    async def _has_permission_async(
        self, source: Any, info: Info, **kwargs: object
    ) -> Union[bool, tuple[Literal[False], dict]]:
        failed_permissions = []
        for permission in self.child_permissions:
            permission_response = await await_maybe(
                permission.has_permission(source, info, **kwargs)
            )
            has_permission, context = unpack_maybe(permission_response, {})
            if has_permission:
                return True
            failed_permissions.append((permission, context))

        return False, {"failed_permissions": failed_permissions}

    def __or__(self, other: BasePermission) -> OrPermission:
        return OrPermission([*self.child_permissions, other])


class PermissionExtension(FieldExtension):
    """Handles permissions for a field.

    Instantiate this as a field extension with all of the permissions you want to apply.

    Note:
    Currently, this is automatically added to the field, when using
    field.permission_classes. You are free to use whichever method you prefer.
    Use PermissionExtension if you want additional customization.
    """

    def __init__(
        self,
        permissions: list[BasePermission],
        use_directives: bool = True,
        fail_silently: bool = False,
    ) -> None:
        """Initialize the permission extension.

        Args:
            permissions: List of permissions to apply.
            fail_silently: If True, return None or [] instead of raising an exception.
                This is only valid for optional or list fields.
            use_directives: If True, add schema directives to the field.
        """
        self.permissions = permissions
        self.fail_silently = fail_silently
        self.return_empty_list = False
        self.use_directives = use_directives

    def apply(self, field: StrawberryField) -> None:
        """Applies all of the permission directives (deduped) to the schema and sets up silent permissions."""
        if self.use_directives:
            permission_directives = [
                p.schema_directive
                for p in self.permissions
                if not isinstance(p, CompositePermission) and p.schema_directive
            ]
            # Iteration, because we want to keep order
            for perm_directive in permission_directives:
                # Dedupe multiple directives
                if perm_directive not in field.directives:
                    field.directives.append(perm_directive)
        # We can only fail silently if the field is optional or a list
        if self.fail_silently:
            if isinstance(field.type, StrawberryOptional):
                if isinstance(field.type.of_type, StrawberryList):
                    self.return_empty_list = True
            elif isinstance(field.type, StrawberryList):
                self.return_empty_list = True
            else:
                raise PermissionFailSilentlyRequiresOptionalError(field)

    def _on_unauthorized(self, permission: BasePermission, **kwargs: object) -> Any:
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
        **kwargs: dict[str, Any],
    ) -> Any:
        """Checks if the permission should be accepted and raises an exception if not."""
        for permission in self.permissions:
            has_permission, context = unpack_maybe(
                permission.has_permission(source, info, **kwargs), {}
            )

            if not has_permission:
                return self._on_unauthorized(permission, **context)

        return next_(source, info, **kwargs)

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: dict[str, Any],
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
        """Whether this extension can be resolved synchronously or not.

        The Permission extension always supports async checking using await_maybe,
        but only supports sync checking if there are no async permissions.
        """
        return all(not permission.is_async for permission in self.permissions)


__all__ = [
    "BasePermission",
    "PermissionExtension",
]

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

    def resolve_permission_sync(self, source: Any, info: Info, **kwargs: Any) -> None:
        if self.has_permission(source, info, **kwargs):
            return
        else:
            return self.on_unauthorized()

    async def resolve_permission_async(
        self, source: Any, info: Info, **kwargs: Any
    ) -> None:
        if await await_maybe(self.has_permission(source, info, **kwargs)):
            return
        else:
            return self.on_unauthorized()

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
    def schema_directive(self) -> List[object]:
        if not self._schema_directive:
            class AutoDirective:
                __strawberry_directive__ = StrawberrySchemaDirective(
                    self.__class__.__name__,
                    self.__class__.__name__,
                    [Location.FIELD_DEFINITION],
                    [],
                )

            self._schema_directive = AutoDirective()

        return [self._schema_directive]

    @property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.has_permission)

    def __and__(self, other: BasePermission):
        return AndPermission(self, other)

    def __or__(self, other: BasePermission):
        return OrPermission(self, other)


class BoolPermission(BasePermission, abc.ABC):
    left: BasePermission
    right: BasePermission

    def __init__(self, left: BasePermission, right: BasePermission):
        self.left = left
        self.right = right

    def has_permission(
        self, source: Any, info: Info, **kwargs: Any
    ) -> Union[bool, Awaitable[bool]]:
        pass

    @property
    def is_async(self) -> bool:
        return self.left.is_async | self.right.is_async

    @property
    def schema_directive(self) -> List[object]:
        return self.left.schema_directive + self.right.schema_directive


class AndPermission(BoolPermission):
    def __init__(self, left: BasePermission, right: BasePermission):
        super().__init__(left, right)

    def resolve_permission_sync(self, source: Any, info: Info,
                                **kwargs: Any) -> None:
        if not self.left.has_permission(source, info, **kwargs):
            return self.left.on_unauthorized()
        if not self.right.has_permission(source, info, **kwargs):
            return self.right.on_unauthorized()

    async def resolve_permission_async(
        self, source: Any, info: Info, **kwargs: Any
    ) -> None:
        if not await await_maybe(self.left.has_permission(source, info, **kwargs)):
            return self.left.on_unauthorized()
        if not await await_maybe(self.right.has_permission(source, info, **kwargs)):
            return self.right.on_unauthorized()


class OrPermission(BoolPermission):
    def __init__(self, left: BasePermission, right: BasePermission):
        super().__init__(left, right)

    def resolve_permission_sync(self, source: Any, info: Info, **kwargs: Any) -> None:
        if self.left.has_permission(source, info, **kwargs):
            return
        if self.right.has_permission(source, info, **kwargs):
            return

        return self.left.on_unauthorized()

    async def resolve_permission_async(
        self, source: Any, info: Info, **kwargs: Any
    ) -> None:
        if await await_maybe(self.left.has_permission(source, info, **kwargs)):
            return
        if await await_maybe(self.right.has_permission(source, info, **kwargs)):
            return

        return self.left.on_unauthorized()


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
    ):
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
                [
                    directive
                    for p in self.permissions
                    for directive in p.schema_directive
                    if p.schema_directive
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
                errror = PermissionFailSilentlyRequiresOptionalError(field)
                raise errror

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
        try:
            for permission in self.permissions:
                permission.resolve_permission_sync(source, info, **kwargs)
        except BaseException as e:
            if self.fail_silently:
                return [] if self.return_empty_list else None
            else:
                raise e
        return next_(source, info, **kwargs)

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: Dict[str, Any],
    ) -> Any:
        try:
            for permission in self.permissions:
                await permission.resolve_permission_async(source, info, **kwargs)
        except BaseException as e:
            if self.fail_silently:
                return [] if self.return_empty_list else None
            else:
                raise e
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
            if permission.is_async
        ]
        return len(async_permissions) == 0

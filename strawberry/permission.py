from __future__ import annotations

import abc
import inspect
from functools import cached_property
from inspect import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
)

from strawberry.exceptions import (
    PermissionReturnedAwaitableInSyncContextError,
    PermissionReturnedNonBooleanError,
    StrawberryGraphQLError,
)
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


def _build_auto_directive(name: str, *, qualname: str, module: str) -> object:
    """Build the auto-generated schema directive object for a permission.

    The returned object carries the `__strawberry_directive__` definition used
    when the permission is added to a field. `qualname` and `module` are copied
    onto its class so collision diagnostics point to something users can rename.
    """

    class AutoDirective:
        __strawberry_directive__ = StrawberrySchemaDirective(
            name,
            name,
            [Location.FIELD_DEFINITION],
            [],
        )

    AutoDirective.__name__ = name
    AutoDirective.__qualname__ = qualname
    AutoDirective.__module__ = module
    return AutoDirective()


_CLASS_OPERAND_HINT = (
    "The `|` operator combines permission instances, not classes. "
    "Instantiate the permission (e.g. `IsAdmin() | IsOwner()`) and pass the "
    "result to `PermissionExtension`."
)


def _is_permission_class(value: object) -> bool:
    return isinstance(value, type) and issubclass(value, BasePermission)


class BasePermission(abc.ABC):
    """Base class for permissions. All permissions should inherit from this class.

    Permission instances can be combined with the `|` operator: the result is an
    `OrPermission` that grants access when any of its operands does. Note that `|`
    combines instances (`IsAdmin() | IsOwner()`), not classes.

    Example:

    ```python
    from strawberry.permission import BasePermission


    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, source, info, **kwargs):
            return info.context["user"].is_authenticated
    ```
    """

    message: str | None = None

    error_extensions: GraphQLErrorExtensions | None = None

    error_class: type[GraphQLError] = StrawberryGraphQLError

    _schema_directive: ClassVar[object | None] = None
    _auto_schema_directive: ClassVar[object]

    def __or__(self, other: BasePermission) -> OrPermission:
        if _is_permission_class(other):
            raise TypeError(_CLASS_OPERAND_HINT)
        if not isinstance(other, BasePermission):
            return NotImplemented
        return OrPermission(self, other)

    def __ror__(self, other: object) -> OrPermission:
        # `IsA | IsB()` lands here once `type.__or__` returns NotImplemented, so
        # the class-operand hint covers a class on either side.
        if _is_permission_class(other):
            raise TypeError(_CLASS_OPERAND_HINT)
        if isinstance(other, BasePermission):
            return OrPermission(other, self)
        return NotImplemented

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Every instance of one permission class must use the same directive
        # definition; otherwise two uses look like conflicting definitions with
        # the same GraphQL name during schema collection. Build it when the
        # permission subclass is created rather than lazily, which also avoids
        # concurrent schema construction racing to create two definitions. Keep
        # it separate from `_schema_directive` so instance, class, and inherited
        # overrides work.
        cls._auto_schema_directive = _build_auto_directive(
            cls.__name__, qualname=cls.__qualname__, module=cls.__module__
        )

    @abc.abstractmethod
    def has_permission(
        self, source: Any, info: Info, **kwargs: Any
    ) -> bool | Awaitable[bool]:
        """Check if the permission should be accepted.

        This method should be overridden by the subclasses.
        """
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )

    def on_unauthorized(self) -> None:
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
        return self._schema_directive or self._auto_schema_directive


# One directive per distinct set of operand classes, so every use of `A() | B()`
# prints the same definition whatever the operand order. Keys keep the operand
# classes alive, which is fine: permission classes live as long as the process.
_composite_directives: dict[tuple[type[BasePermission], ...], object] = {}


def _get_composite_directive(permissions: tuple[BasePermission, ...]) -> object:
    classes = tuple(
        sorted(
            (type(p) for p in permissions),
            # Total order even for distinct classes with identical metadata (e.g.
            # made by a factory), so `A() | B()` and `B() | A()` share a directive.
            key=lambda c: (c.__name__, c.__module__, c.__qualname__, id(c)),
        )
    )
    directive = _composite_directives.get(classes)
    if directive is None:
        name = "Or".join(c.__name__ for c in classes)
        operands = " | ".join(f"{c.__module__}.{c.__qualname__}" for c in classes)
        # `setdefault` is atomic, so a racing duplicate is simply discarded.
        directive = _composite_directives.setdefault(
            classes,
            _build_auto_directive(
                name,
                qualname=f"{name}({operands})",
                module=__name__,
            ),
        )
    return directive


class OrPermission(BasePermission):
    """Grants access when any of the combined permissions does.

    Usually created with the `|` operator. Permissions are evaluated left to
    right and evaluation stops at the first one that grants access. Operands may
    be sync or async. Nested compositions are flattened, so `(A | B) | C` is the
    same as `A | B | C`.

    When no operand grants access, the first operand's `on_unauthorized` is used.
    Subclass `OrPermission` to give a combination its own name, `message` and
    error handling, or to override `has_permission` altogether. A plain
    combination is flattened when combined further, so attributes set on it are
    not carried over.

    Example:

    ```python
    import strawberry
    from strawberry.permission import BasePermission, PermissionExtension


    class IsAdmin(BasePermission):
        message = "User is not an admin"

        def has_permission(self, source, info, **kwargs):
            return info.context["user"].is_admin


    class IsOwner(BasePermission):
        message = "User is not the owner"

        def has_permission(self, source, info, **kwargs):
            return info.context["user"].id == source.owner_id


    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension([IsAdmin() | IsOwner()])])
        def secret(self) -> str:
            return "secret"
    ```
    """

    permissions: tuple[BasePermission, ...]

    def __init__(self, *permissions: BasePermission) -> None:
        flattened: list[BasePermission] = []
        for permission in permissions:
            if not isinstance(permission, BasePermission):
                raise TypeError(
                    "OrPermission operands must be BasePermission instances, "
                    f"got {permission!r}"
                )
            if type(permission) is OrPermission:
                flattened.extend(permission.permissions)
            else:
                flattened.append(permission)

        if len(flattened) < 2:
            raise ValueError("OrPermission requires at least two permissions")

        self.permissions = tuple(flattened)

        # `PermissionExtension.supports_sync` picks the sync or async path with
        # `iscoroutinefunction(has_permission)`, so expose the async
        # implementation as an instance attribute only when an operand is async.
        # The operands are checked as written rather than flattened: a flattened
        # composite already reports whether any of its operands is async. A
        # subclass that overrides `has_permission` keeps its override.
        if type(self).has_permission is OrPermission.has_permission and any(
            iscoroutinefunction(p.has_permission) for p in permissions
        ):
            self.has_permission = self._has_permission_async  # type: ignore[method-assign]

    def has_permission(
        self, source: Any, info: Info, **kwargs: Any
    ) -> bool | Awaitable[bool]:
        # Instances are shared between requests and concurrent executions, so
        # nothing per-request is stored on `self` here or in the async variant.
        for permission in self.permissions:
            result = permission.has_permission(source, info, **kwargs)

            # Mirror `PermissionExtension.resolve`: an awaitable is truthy, so
            # trusting it would silently grant access. Fail closed.
            if inspect.isawaitable(result):
                if inspect.iscoroutine(result):
                    result.close()

                raise PermissionReturnedAwaitableInSyncContextError(permission)

            if result:
                return True

        return False

    async def _has_permission_async(
        self, source: Any, info: Info, **kwargs: Any
    ) -> bool:
        # Sequential on purpose: operands may be expensive or have side effects,
        # and evaluation order is part of the contract.
        for permission in self.permissions:
            result = await await_maybe(
                permission.has_permission(source, info, **kwargs)
            )
            if result:
                return True

        return False

    def on_unauthorized(self) -> None:
        if type(self) is OrPermission:
            # Every operand denied access, so there is no "failing" operand to
            # pick: use the first one, the primary permission the author wrote.
            self.permissions[0].on_unauthorized()
        else:
            super().on_unauthorized()

    @property
    def schema_directive(self) -> object:
        # Looked up on first use rather than in `__init__`: chaining
        # `A() | B() | C()` builds `A() | B()` on the way, and that intermediate
        # never needs a directive. Nothing is cached on the instance, so
        # `copy`/`deepcopy` keep directive identity for the identity-based dedup
        # in `PermissionExtension.apply`.
        return self._schema_directive or (
            _get_composite_directive(self.permissions)
            if type(self) is OrPermission
            else self._auto_schema_directive
        )


class PermissionExtension(FieldExtension):
    """Handles permissions for a field.

    Instantiate this as a field extension with all of the permissions you want to apply.

    Note:
        Currently, this is automatically added to the field, when using field.permission_classes

    This is deprecated behaviour, please manually add the extension to field.extensions
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
                perm.schema_directive
                for perm in self.permissions
                if perm.schema_directive
            ]
            # Iteration, because we want to keep order
            for perm_directive in permission_directives:
                # Dedupe multiple directives
                if perm_directive in field.directives:
                    continue
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

    def _on_unauthorized(self, permission: BasePermission) -> Any:
        if self.fail_silently:
            return [] if self.return_empty_list else None
        return permission.on_unauthorized()

    def resolve(
        self,
        next_: SyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: dict[str, Any],
    ) -> Any:
        """Checks if the permission should be accepted and raises an exception if not."""
        for permission in self.permissions:
            has_permission = permission.has_permission(source, info, **kwargs)

            # A permission whose `has_permission` returns an awaitable (e.g. a
            # plain `def` returning a coroutine) cannot be resolved here: the
            # awaitable is truthy regardless of what it resolves to, so trusting
            # it would silently grant access. `supports_sync` only detects
            # `async def` via `iscoroutinefunction`, so this case reaches the
            # sync path. Fail closed instead of leaking the field.
            if inspect.isawaitable(has_permission):
                # Close the coroutine so we don't leak a "coroutine was never
                # awaited" warning on top of the error we are about to raise.
                if inspect.iscoroutine(has_permission):
                    has_permission.close()

                raise PermissionReturnedAwaitableInSyncContextError(permission)

            # Only a real boolean decides access. Anything else, such as the
            # truthy async generator returned by an `async def` that `yield`s,
            # is rejected rather than evaluated for truthiness.
            if not isinstance(has_permission, bool):
                raise PermissionReturnedNonBooleanError(permission, has_permission)

            if not has_permission:
                return self._on_unauthorized(permission)

        return next_(source, info, **kwargs)

    async def resolve_async(
        self,
        next_: AsyncExtensionResolver,
        source: Any,
        info: Info,
        **kwargs: dict[str, Any],
    ) -> Any:
        for permission in self.permissions:
            has_permission = await await_maybe(
                permission.has_permission(source, info, **kwargs)
            )

            if not isinstance(has_permission, bool):
                # e.g. an `async def` returning a coroutine; close it so it
                # doesn't also warn about never being awaited.
                if inspect.iscoroutine(has_permission):
                    has_permission.close()

                raise PermissionReturnedNonBooleanError(permission, has_permission)

            if not has_permission:
                return self._on_unauthorized(permission)
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
        async_permissions = [
            True
            for permission in self.permissions
            if iscoroutinefunction(permission.has_permission)
        ]
        return len(async_permissions) == 0


__all__ = [
    "BasePermission",
    "OrPermission",
    "PermissionExtension",
]

import copy
import inspect
from collections.abc import Awaitable
from typing import Any

import pytest

from strawberry.exceptions import PermissionReturnedAwaitableInSyncContextError
from strawberry.permission import BasePermission, OrPermission, PermissionExtension
from strawberry.schema_directive import StrawberrySchemaDirective
from strawberry.types import Info


class Allowed(BasePermission):
    message = "Allowed"

    def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        return True


class Denied(BasePermission):
    message = "Denied"

    def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        return False


class AsyncAllowed(BasePermission):
    message = "Async allowed"

    async def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        return True


class AsyncDenied(BasePermission):
    message = "Async denied"

    async def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        return False


def make_counting_permission(result: bool) -> type[BasePermission]:
    class Counting(BasePermission):
        def __init__(self) -> None:
            self.calls = 0

        def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
            self.calls += 1
            return result

    return Counting


def directive_name(permission: BasePermission) -> str:
    directive = permission.schema_directive
    definition = directive.__strawberry_directive__  # type: ignore[attr-defined]
    assert isinstance(definition, StrawberrySchemaDirective)
    return definition.python_name


def test_or_returns_or_permission_with_operands_in_order():
    a, b = Allowed(), Denied()

    combined = a | b

    assert isinstance(combined, OrPermission)
    assert combined.permissions == (a, b)


def test_or_flattens_nested_compositions_in_written_order():
    class C(Allowed):
        pass

    a, b, c = Allowed(), Denied(), C()

    assert (a | b | c).permissions == (a, b, c)
    assert ((a | b) | c).permissions == (a, b, c)
    assert (a | (b | c)).permissions == (a, b, c)
    assert OrPermission(a, OrPermission(b, c)).permissions == (a, b, c)


def test_or_does_not_flatten_subclasses_of_or_permission():
    class AdminOrOwner(OrPermission):
        pass

    a, b, c = Allowed(), Denied(), Allowed()
    named = AdminOrOwner(a, b)

    combined = named | c

    assert combined.permissions == (named, c)
    assert (c | named).permissions == (c, named)


def test_or_with_non_permission_operand_raises_type_error():
    with pytest.raises(TypeError):
        Allowed() | 1  # type: ignore[operator]

    with pytest.raises(TypeError):
        1 | Allowed()  # type: ignore[operator]

    with pytest.raises(TypeError):
        Allowed() | None  # type: ignore[operator]


def test_or_with_permission_class_on_the_right_hints_to_instantiate():
    with pytest.raises(TypeError, match="Instantiate"):
        Allowed() | Denied


def test_or_with_permission_class_on_the_left_hints_to_instantiate():
    with pytest.raises(TypeError, match="Instantiate"):
        Allowed | Denied()


def test_ror_with_permission_instance_composes_in_written_order():
    a, b = Allowed(), Denied()

    combined = b.__ror__(a)

    assert isinstance(combined, OrPermission)
    assert combined.permissions == (a, b)


def test_or_permission_requires_at_least_two_permissions():
    with pytest.raises(ValueError, match="at least two"):
        OrPermission()

    with pytest.raises(ValueError, match="at least two"):
        OrPermission(Allowed())


def test_or_permission_rejects_non_permission_operands():
    with pytest.raises(TypeError):
        OrPermission(Allowed(), 1)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        OrPermission(Allowed(), Denied)  # type: ignore[arg-type]


def test_or_permission_has_no_message_of_its_own():
    assert (Allowed() | Denied()).message is None


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (Denied, Denied, False),
        (Denied, Allowed, True),
        (Allowed, Denied, True),
        (Allowed, Allowed, True),
    ],
)
def test_sync_truth_table(
    left: type[BasePermission], right: type[BasePermission], expected: bool
):
    combined = left() | right()

    assert combined.has_permission(None, None) is expected  # type: ignore[arg-type]
    assert not inspect.iscoroutinefunction(combined.has_permission)


def test_sync_short_circuits_left_to_right():
    Yes = make_counting_permission(True)
    No = make_counting_permission(False)

    yes, no = Yes(), No()
    assert (yes | no).has_permission(None, None) is True
    assert (yes.calls, no.calls) == (1, 0)

    yes, no = Yes(), No()
    assert (no | yes).has_permission(None, None) is True
    assert (no.calls, yes.calls) == (1, 1)

    first, second = No(), No()
    assert (first | second).has_permission(None, None) is False
    assert (first.calls, second.calls) == (1, 1)


def test_kwargs_are_forwarded_to_every_operand():
    received: list[dict[str, Any]] = []

    class Recording(BasePermission):
        def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
            received.append(kwargs)
            return False

    (Recording() | Recording()).has_permission(None, None, name="a", age=1)  # type: ignore[arg-type]

    assert received == [{"name": "a", "age": 1}] * 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (AsyncDenied, AsyncDenied, False),
        (AsyncDenied, AsyncAllowed, True),
        (AsyncAllowed, AsyncDenied, True),
        (AsyncAllowed, AsyncAllowed, True),
    ],
)
async def test_async_truth_table(
    left: type[BasePermission], right: type[BasePermission], expected: bool
):
    combined = left() | right()

    result = await combined.has_permission(None, None)  # type: ignore[arg-type,misc]

    assert result is expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (Denied, AsyncDenied, False),
        (Denied, AsyncAllowed, True),
        (AsyncDenied, Allowed, True),
        (AsyncDenied, Denied, False),
        (Allowed, AsyncDenied, True),
        (AsyncAllowed, Denied, True),
    ],
)
async def test_mixed_sync_and_async_operands(
    left: type[BasePermission], right: type[BasePermission], expected: bool
):
    combined = left() | right()

    result = await combined.has_permission(None, None)  # type: ignore[arg-type,misc]

    assert result is expected


@pytest.mark.asyncio
async def test_async_short_circuits_left_to_right():
    calls: list[str] = []

    class FirstAsync(BasePermission):
        async def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
            calls.append("first")
            return True

    class Second(BasePermission):
        def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
            calls.append("second")
            return True

    await (FirstAsync() | Second()).has_permission(None, None)  # type: ignore[arg-type,misc]
    assert calls == ["first"]

    calls.clear()
    await (Second() | FirstAsync()).has_permission(None, None)  # type: ignore[arg-type,misc]
    assert calls == ["second"]


def test_has_permission_is_coroutine_function_iff_any_operand_is_async():
    assert not inspect.iscoroutinefunction((Allowed() | Denied()).has_permission)
    assert inspect.iscoroutinefunction((Allowed() | AsyncDenied()).has_permission)
    assert inspect.iscoroutinefunction((AsyncAllowed() | Denied()).has_permission)
    assert inspect.iscoroutinefunction((AsyncAllowed() | AsyncDenied()).has_permission)


def test_permission_extension_supports_sync_only_when_or_permission_has_no_async_operand():
    assert PermissionExtension([Allowed() | Denied()]).supports_sync
    assert not PermissionExtension([Allowed() | AsyncDenied()]).supports_sync
    assert not PermissionExtension(
        [Allowed() | (Denied() | AsyncAllowed())]
    ).supports_sync


def test_async_detection_propagates_through_nesting():
    class AsyncOrSubclass(OrPermission):
        pass

    sync_only = Allowed() | Denied()
    with_async = Allowed() | AsyncDenied()

    assert inspect.iscoroutinefunction((sync_only | Allowed()).has_permission) is False
    assert inspect.iscoroutinefunction((with_async | Allowed()).has_permission)
    assert inspect.iscoroutinefunction((Allowed() | with_async).has_permission)
    assert inspect.iscoroutinefunction(
        (Allowed() | AsyncOrSubclass(Allowed(), AsyncDenied())).has_permission
    )
    assert not inspect.iscoroutinefunction(
        (Allowed() | AsyncOrSubclass(Allowed(), Denied())).has_permission
    )


def test_subclass_overriding_has_permission_is_not_replaced_by_async_operands():
    class StrictDeny(OrPermission):
        def has_permission(
            self, source: Any, info: Info, **kwargs: Any
        ) -> bool | Awaitable[bool]:
            return False

    combined = StrictDeny(Allowed(), AsyncAllowed())

    assert "has_permission" not in vars(combined)
    assert not inspect.iscoroutinefunction(combined.has_permission)
    assert combined.has_permission(None, None) is False  # type: ignore[arg-type]


def test_sync_operand_returning_coroutine_fails_closed_and_closes_it():
    created: list[Any] = []

    class ReturnsCoroutine(BasePermission):
        def has_permission(self, source: Any, info: Info, **kwargs: Any) -> Any:
            coro = self._check()
            created.append(coro)
            return coro

        async def _check(self) -> bool:
            return True  # pragma: no cover

    combined = Denied() | ReturnsCoroutine()
    assert not inspect.iscoroutinefunction(combined.has_permission)

    with pytest.raises(
        PermissionReturnedAwaitableInSyncContextError, match="ReturnsCoroutine"
    ):
        combined.has_permission(None, None)  # type: ignore[arg-type]

    # an un-closed coroutine would only warn "never awaited" when collected
    assert len(created) == 1
    assert inspect.getcoroutinestate(created[0]) == inspect.CORO_CLOSED


def test_earlier_granting_operand_short_circuits_before_awaitable_operand():
    class ReturnsCoroutine(BasePermission):
        def has_permission(self, source: Any, info: Info, **kwargs: Any) -> Any:
            return self._check()

        async def _check(self) -> bool:
            return True  # pragma: no cover

    # The bad operand is never reached, so nothing is raised.
    assert (Allowed() | ReturnsCoroutine()).has_permission(None, None) is True  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_async_path_awaits_sync_operand_returning_coroutine():
    class ReturnsCoroutine(BasePermission):
        def has_permission(self, source: Any, info: Info, **kwargs: Any) -> Any:
            return self._check()

        async def _check(self) -> bool:
            return True

    combined = AsyncDenied() | ReturnsCoroutine()

    assert await combined.has_permission(None, None) is True  # type: ignore[arg-type,misc]


def test_on_unauthorized_delegates_to_first_operand():
    class FirstError(Exception):
        pass

    class First(BasePermission):
        message = "first"

        def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
            return False

        def on_unauthorized(self) -> None:
            raise FirstError(self.message)

    with pytest.raises(FirstError, match="first"):
        (First() | Denied()).on_unauthorized()

    with pytest.raises(FirstError, match="first"):
        (First() | Denied() | Allowed()).on_unauthorized()


def test_on_unauthorized_raises_first_operand_error_by_default():
    with pytest.raises(Exception, match="Denied") as exc_info:
        (Denied() | Allowed()).on_unauthorized()

    assert str(exc_info.value) == "Denied"


def test_on_unauthorized_of_subclass_uses_its_own_error():
    class AdminOrOwner(OrPermission):
        message = "Needs admin or owner"

    with pytest.raises(Exception, match="Needs admin or owner"):
        AdminOrOwner(Denied(), Allowed()).on_unauthorized()


def test_on_unauthorized_of_subclass_uses_its_own_error_class_and_extensions():
    class CustomError(Exception):
        def __init__(self, message: str) -> None:
            super().__init__(message)
            self.extensions: dict[str, Any] | None = None

    class AdminOrOwner(OrPermission):
        message = "Needs admin or owner"
        error_class = CustomError  # type: ignore[assignment]
        error_extensions = {"code": "FORBIDDEN"}

    with pytest.raises(CustomError) as exc_info:
        AdminOrOwner(Denied(), Allowed()).on_unauthorized()

    assert exc_info.value.extensions == {"code": "FORBIDDEN"}


def test_on_unauthorized_of_subclass_can_be_overridden():
    class CustomError(Exception):
        pass

    class AdminOrOwner(OrPermission):
        def on_unauthorized(self) -> None:
            raise CustomError("custom")

    with pytest.raises(CustomError, match="custom"):
        AdminOrOwner(Denied(), Allowed()).on_unauthorized()


def test_directive_is_the_same_object_regardless_of_order():
    class IsAdmin(Allowed):
        pass

    class IsOwner(Allowed):
        pass

    first = IsAdmin() | IsOwner()
    second = IsOwner() | IsAdmin()

    assert first.schema_directive is second.schema_directive
    assert first.schema_directive is (IsAdmin() | IsOwner()).schema_directive


def test_directive_name_is_sorted_and_flat():
    class IsAdmin(Allowed):
        pass

    class IsOwner(Allowed):
        pass

    class IsStaff(Allowed):
        pass

    assert directive_name(IsOwner() | IsAdmin()) == "IsAdminOrIsOwner"
    assert directive_name(IsStaff() | IsOwner() | IsAdmin()) == (
        "IsAdminOrIsOwnerOrIsStaff"
    )
    assert directive_name(IsStaff() | (IsOwner() | IsAdmin())) == (
        "IsAdminOrIsOwnerOrIsStaff"
    )


def test_directive_name_for_same_class_with_different_arguments():
    class HasRole(BasePermission):
        def __init__(self, role: str) -> None:
            self.role = role

        def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
            return False

    combined = HasRole("admin") | HasRole("editor")

    assert len(combined.permissions) == 2
    assert directive_name(combined) == "HasRoleOrHasRole"
    assert combined.schema_directive is not HasRole("admin").schema_directive
    assert combined.schema_directive is (HasRole("a") | HasRole("b")).schema_directive


def test_directive_cache_is_keyed_by_class_not_name():
    first = type("CanAccess", (Allowed,), {"__module__": "permissions.first"})
    second = type("CanAccess", (Allowed,), {"__module__": "permissions.second"})

    from_first = first() | Denied()
    from_second = second() | Denied()

    assert directive_name(from_first) == directive_name(from_second)
    assert from_first.schema_directive is not from_second.schema_directive

    assert directive_name(from_first) == "CanAccessOrDenied"


def test_chaining_creates_no_directives_for_intermediate_compositions():
    classes = [type(f"Step{i}", (Allowed,), {}) for i in range(4)]
    cached = len(OrPermission._directive_cache)

    combined = classes[0]() | classes[1]() | classes[2]() | classes[3]()
    assert len(OrPermission._directive_cache) == cached

    combined.schema_directive
    assert len(OrPermission._directive_cache) == cached + 1
    assert directive_name(combined) == "Step0OrStep1OrStep2OrStep3"


def test_directive_diagnostics_name_the_constituent_classes():
    first = type("CanAccess", (Allowed,), {"__module__": "permissions.first"})
    second = type("CanAccess", (Allowed,), {"__module__": "permissions.second"})

    directive = (first() | second()).schema_directive

    assert type(directive).__module__ == "strawberry.permission"
    assert "permissions.first.CanAccess" in type(directive).__qualname__
    assert "permissions.second.CanAccess" in type(directive).__qualname__


def test_schema_directive_override_on_instance_wins():
    class Custom:
        pass

    custom = Custom()
    combined = Allowed() | Denied()
    combined._schema_directive = custom  # type: ignore[misc]

    assert combined.schema_directive is custom


def test_schema_directive_override_on_subclass_wins():
    class Custom:
        pass

    custom = Custom()

    class AdminOrOwner(OrPermission):
        _schema_directive = custom

    assert AdminOrOwner(Allowed(), Denied()).schema_directive is custom


def test_schema_directive_override_inherited_by_subclass_wins():
    class Custom:
        pass

    custom = Custom()

    class Base(OrPermission):
        _schema_directive = custom

    class Child(Base):
        pass

    assert Child(Allowed(), Denied()).schema_directive is custom


def test_directive_is_the_same_object_for_classes_with_identical_metadata():
    def make_permission() -> type[BasePermission]:
        class Same(BasePermission):
            def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
                return True

        return Same

    first, second = make_permission(), make_permission()
    assert first is not second
    assert (first.__name__, first.__module__, first.__qualname__) == (
        second.__name__,
        second.__module__,
        second.__qualname__,
    )

    assert (first() | second()).schema_directive is (
        second() | first()
    ).schema_directive


@pytest.mark.parametrize("copier", [copy.copy, copy.deepcopy])
def test_copies_of_a_composite_keep_the_directive_identity(copier: Any):
    combined = Allowed() | Denied()

    assert copier(combined).schema_directive is combined.schema_directive


def test_subclass_of_or_permission_uses_its_own_directive():
    class AdminOrOwner(OrPermission):
        pass

    combined = AdminOrOwner(Allowed(), Denied())

    assert directive_name(combined) == "AdminOrOwner"
    assert combined.schema_directive is AdminOrOwner._auto_schema_directive
    assert combined.schema_directive is not (Allowed() | Denied()).schema_directive


def test_subclass_of_or_permission_with_fixed_operands():
    class AdminOrOwner(OrPermission):
        def __init__(self) -> None:
            super().__init__(Allowed(), Denied())

    combined = AdminOrOwner()

    assert combined.permissions[0].__class__ is Allowed
    assert directive_name(combined) == "AdminOrOwner"

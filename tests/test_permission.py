from typing import Any

from strawberry.permission import BasePermission
from strawberry.types import Info


def test_or_permission_condition():
    class AllowedPermission(BasePermission):
        message = "Allowed"

        def has_permission(self, source: Any, info: Info, **kwargs: Any):
            return True

    class DeniedPermission(BasePermission):
        message = "Denied"

        def has_permission(self, source: Any, info: Info, **kwargs: Any):
            return False

    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, source: Any, info: Info, **kwargs: Any):
            return False

    # cases with all `has_permission(...) == False` should deny on the last
    denied_permission = DeniedPermission()
    not_a_or_not_b = IsAuthenticated() | denied_permission
    assert not_a_or_not_b.has_permission(None, None) is False
    assert not_a_or_not_b.message == denied_permission.message
    assert not_a_or_not_b.on_unauthorized == denied_permission.on_unauthorized

    # cases with any true should allow
    not_a_or_b = DeniedPermission() | AllowedPermission()
    a_or_not_b = AllowedPermission() | DeniedPermission()
    a_or_b = AllowedPermission() | AllowedPermission()
    assert not_a_or_b.has_permission(None, None) is True
    assert a_or_not_b.has_permission(None, None) is True
    assert a_or_b.has_permission(None, None) is True


def test_or_permission_async_to_sync():
    class AllowedPermission(BasePermission):
        message = "Allowed"

        def has_permission(self, source: Any, info: Info, **kwargs: Any):
            return True

    class DeniedPermission(BasePermission):
        message = "Denied"

        async def has_permission(self, source: Any, info: Info, **kwargs: Any):
            return False

    class IsAuthenticated(BasePermission):
        message = "User is not authenticated"

        def has_permission(self, source: Any, info: Info, **kwargs: Any):
            return False

    # cases with all `has_permission(...) == False` should deny on the last
    denied_permission = DeniedPermission()
    not_a_or_not_b = IsAuthenticated() | denied_permission
    assert not_a_or_not_b.has_permission(None, None) is False
    assert not_a_or_not_b.message == denied_permission.message
    assert not_a_or_not_b.on_unauthorized == denied_permission.on_unauthorized

    # cases with any true should allow
    not_a_or_b = DeniedPermission() | AllowedPermission()
    a_or_not_b = AllowedPermission() | DeniedPermission()
    a_or_b = AllowedPermission() | AllowedPermission()
    assert not_a_or_b.has_permission(None, None) is True
    assert a_or_not_b.has_permission(None, None) is True
    assert a_or_b.has_permission(None, None) is True

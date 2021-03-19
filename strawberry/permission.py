from typing import Any

from strawberry.types.info import Info


class BasePermission:
    """
    Base class for creating permissions
    """

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )

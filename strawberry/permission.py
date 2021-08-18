from typing import Any, Awaitable, Optional, Union

from strawberry.types.info import Info


class BasePermission:
    """
    Base class for creating permissions
    """

    message: Optional[str] = None

    def has_permission(
        self, source: Any, info: Info, **kwargs
    ) -> Union[bool, Awaitable[bool]]:
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )

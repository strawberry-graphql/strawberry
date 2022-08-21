from typing import Any, Awaitable, Optional, Union

from strawberry.types.info import Info

from .object_type import interface


@interface
class PermissionInterface:
    success: bool


class BasePermission:
    """
    Base class for creating permissions
    """

    def __init_subclass__(cls, **kwargs):
        cls.return_type = cls.has_permission.__annotations__["return"]

    message: Optional[str] = None
    return_type: Any = None

    def has_permission(
        self, source: Any, info: Info, **kwargs
    ) -> Union[
        bool, Awaitable[bool], PermissionInterface, Awaitable[PermissionInterface]
    ]:
        raise NotImplementedError(
            "Permission classes should override has_permission method"
        )

from typing import Any, Awaitable, Optional, Union, get_type_hints

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
        if return_type := get_type_hints(cls.has_permission).get("return"):
            if not isinstance(return_type, bool) and cls.message:
                raise RuntimeError(
                    "Permission classes that are returning bool,"
                    "must not declare `message` this is redundant."
                )
        else:
            raise RuntimeError("has_permission method must declare a return type")
        cls.return_type = return_type

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

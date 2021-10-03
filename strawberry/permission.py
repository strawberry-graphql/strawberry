import abc
from typing import TYPE_CHECKING, Any, Awaitable, Optional, Union
from warnings import warn

from strawberry.type import StrawberryOptional
from strawberry.types.info import Info


if TYPE_CHECKING:
    from strawberry.field import StrawberryField


class BasePermission(abc.ABC):
    """
    Base class for creating permissions
    """

    message: Optional[str] = None

    @abc.abstractclassmethod
    def has_permission(
        self, source: Any, info: Info, **kwargs
    ) -> Union[bool, Awaitable[bool]]:
        ...

    @classmethod
    def assert_valid_for_field(cls, field: "StrawberryField") -> None:
        # assert all abstact methods are implemented in a subclass
        not_implemented_methods = getattr(cls, "__abstractmethods__", None)
        if not_implemented_methods:
            method_names = ", ".join(not_implemented_methods)
            raise NotImplementedError(
                f"Permission class {cls.__name__} "
                f"should have the following methods implemented: {method_names}"
            )

        # check that field can retrun `null` if permission check doesn't pass
        if not isinstance(field.type, StrawberryOptional):
            documentation_link = (
                "https://strawberry.rocks/docs/guides/"
                "permissions#setting-permissions-on-non-optional-fields"
            )
            warn(
                f"Setting permission class on a non-optional field '{field.name}'. "
                f"For more details check the documentation: {documentation_link}"
            )

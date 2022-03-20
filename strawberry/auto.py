from typing import Any, ClassVar, Optional, Union, cast

from typing_extensions import Annotated, Final, get_args, get_origin

from strawberry.type import StrawberryType

from .annotation import StrawberryAnnotation


class StrawberryAuto:
    _instance: ClassVar[Optional["StrawberryAuto"]] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            return cls._instance

        cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __str__(self):
        return "auto"

    def __repr__(self):
        return "<auto>"


auto: Final = Annotated[Any, StrawberryAuto()]


def is_auto(type_: Union[StrawberryAnnotation, StrawberryType, type]):
    if isinstance(type_, StrawberryAnnotation):
        resolved = type_.annotation
        if isinstance(resolved, str):
            namespace = type_.namespace
            resolved = namespace and namespace.get(resolved)

        if resolved is not None:
            type_ = cast(type, resolved)

    if type_ is auto:
        return True

    # Support uses of Annotated[auto, something()]
    if get_origin(type_) is Annotated:
        args = get_args(type_)
        if args[0] is Any:
            return any(isinstance(arg, StrawberryAuto) for arg in args[1:])

    return False

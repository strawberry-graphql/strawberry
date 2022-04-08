from __future__ import annotations

from typing import Any, Optional, Union, cast

from typing_extensions import Annotated, Final

from strawberry.type import StrawberryAnnotated, StrawberryType

from .annotation import StrawberryAnnotation


class StrawberryAutoMeta(type):
    """Metaclass for StrawberryAuto.

    This is used to make sure StrawberryAuto is a singleton and also to
    override the behavior of `isinstance` so that it consider the following
    cases:

        >> isinstance(StrawberryAuto(), StrawberryAuto)
        True
        >> isinstance(StrawberryAnnotation(StrawberryAuto()), StrawberryAuto)
        True
        >> isinstance(Annotated[StrawberryAuto(), object()), StrawberryAuto)
        True

    """

    def __init__(self, *args, **kwargs):
        self._instance: Optional[StrawberryAuto] = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)

        return cls._instance

    def __instancecheck__(
        self,
        instance: Union[StrawberryAnnotation, StrawberryType, type],
    ):
        if isinstance(instance, StrawberryAnnotation):
            resolved = instance.annotation
            if isinstance(resolved, str):
                namespace = instance.namespace
                resolved = namespace and namespace.get(resolved)

            if resolved is None:
                return False

            instance = cast(type, resolved)

        if instance is auto:
            return True

        # Support uses of Annotated[auto, something()]
        instance, args = StrawberryAnnotated.get_type_and_args(instance)
        if instance is Any:
            return any(isinstance(arg, StrawberryAuto) for arg in args)

        return False


class StrawberryAuto(metaclass=StrawberryAutoMeta):
    def __str__(self):
        return "auto"

    def __repr__(self):
        return "<auto>"


auto: Final = Annotated[Any, StrawberryAuto()]

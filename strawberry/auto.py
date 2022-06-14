from __future__ import annotations

from typing import Any, Optional, Union

from typing_extensions import Annotated

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
        # resolve StrawberryAnnotations
        if isinstance(instance, StrawberryAnnotation):
            instance = instance.resolve()

        # Look for Annotated[Any, StrawberryAuto, ...]
        instance, args = StrawberryAnnotated.get_type_and_args(instance)
        return instance is Any and any(isinstance(arg, StrawberryAuto) for arg in args)


class StrawberryAuto(metaclass=StrawberryAutoMeta):
    def __str__(self):
        return "auto"

    def __repr__(self):
        return "<auto>"


auto = Annotated[Any, StrawberryAuto()]

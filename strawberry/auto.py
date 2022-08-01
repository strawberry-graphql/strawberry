from __future__ import annotations

from typing import Any, Optional, Union, cast

from typing_extensions import Annotated, get_args, get_origin

from strawberry.type import StrawberryType

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
        instance: Union[StrawberryAuto, StrawberryAnnotation, StrawberryType, type],
    ):
        if isinstance(instance, StrawberryAnnotation):
            resolved = instance.annotation
            if isinstance(resolved, str):
                namespace = instance.namespace
                resolved = namespace and namespace.get(resolved)

            if resolved is not None:
                instance = cast(type, resolved)

        if instance is auto:
            return True

        # Support uses of Annotated[auto, something()]
        if get_origin(instance) is Annotated:
            args = get_args(instance)
            if args[0] is Any:
                return any(isinstance(arg, StrawberryAuto) for arg in args[1:])

        # We can't compare StrawberryType subclasses to str because it will try to
        # resolve the annotation in its __eq__ method and that might raise a
        # NameError if "strawberry.auto" is not present in locals()/globals()
        # It is not a problem though since StrawberryType subclasses for sure are
        # not auto objects
        if isinstance(instance, StrawberryType):
            return False

        return instance == "strawberry.auto"


class StrawberryAuto(metaclass=StrawberryAutoMeta):
    def __str__(self):
        return "auto"

    def __repr__(self):
        return "<auto>"


auto = Annotated[Any, StrawberryAuto()]

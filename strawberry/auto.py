from __future__ import annotations

from typing import Any, Optional, Union, cast

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
            resolved = instance.annotation
            if isinstance(resolved, str):
                namespace = instance.namespace
                resolved = namespace and namespace.get(resolved)

            if resolved is not None:
                instance = cast(type, resolved)

        if instance is auto:
            return True

        # Support uses of Annotated[auto, something()]
        annotated_type, annotated_args = StrawberryAnnotated.get_type_and_args(instance)
        if annotated_type is Any and any(
            isinstance(arg, StrawberryAuto) for arg in annotated_args
        ):
            return True

        # StrawberryType's `__eq__` tries to find the string passed in the global
        # namespace, which will fail with a `NameError` if "strawberry.auto" hasn't
        # been imported. So we can't use `instance == "strawberry.auto"` here.
        # Instead, we'll use `isinstance(instance, str)` to check if the instance
        # is a StrawberryType, in that case we can return False since we know it
        # won't be a StrawberryAuto.
        if isinstance(instance, StrawberryType):
            return False

        return instance == "strawberry.auto"


class StrawberryAuto(metaclass=StrawberryAutoMeta):
    def __str__(self):
        return "auto"

    def __repr__(self):
        return "<auto>"


auto = Annotated[Any, StrawberryAuto()]

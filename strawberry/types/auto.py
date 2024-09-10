from __future__ import annotations

from typing import Any, Optional, Union, cast
from typing_extensions import Annotated, get_args, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import StrawberryType


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

    def __init__(self, *args: str, **kwargs: Any) -> None:
        self._instance: Optional[StrawberryAuto] = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args: str, **kwargs: Any) -> Any:
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)

        return cls._instance

    def __instancecheck__(
        self,
        instance: Union[StrawberryAuto, StrawberryAnnotation, StrawberryType, type],
    ) -> bool:
        if isinstance(instance, StrawberryAnnotation):
            resolved = instance.raw_annotation
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
    def __str__(self) -> str:
        return "auto"

    def __repr__(self) -> str:
        return "<auto>"


auto = Annotated[Any, StrawberryAuto()]
"""Special marker for automatic annotation.

A special value that can be used to automatically infer the type of a field
when using integrations like Strawberry Django or Strawberry Pydantic.

Example:
```python
import strawberry

from my_user_app import models


@strawberry.django.type(models.User)
class User:
    name: strawberry.auto
```
"""

__all__ = ["auto"]

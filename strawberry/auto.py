from typing import Any, ClassVar, Optional

from typing_extensions import Annotated, Final


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

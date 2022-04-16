import warnings
from typing import Any, Optional, Type


class UnsetType:
    __instance: Optional["UnsetType"] = None

    def __new__(cls: Type["UnsetType"]) -> "UnsetType":
        if cls.__instance is None:
            ret = super().__new__(cls)
            cls.__instance = ret
            return ret
        else:
            return cls.__instance

    def __str__(self):
        return ""

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self):
        return False


UNSET: Any = UnsetType()


def is_unset(value: Any) -> bool:
    warnings.warn("`is_unset` is deprecated use `value is UNSET` instead")
    return value is UNSET


__all__ = [
    "UNSET",
]

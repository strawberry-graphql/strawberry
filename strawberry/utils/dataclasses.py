from __future__ import annotations

import sys
from dataclasses import (  # type: ignore
    _FIELD,
    _FIELD_INITVAR,
    _FIELDS,
    _MISSING_TYPE,
    _POST_INIT_NAME,
    _set_new_attribute,
)
from typing import Any
from typing_extensions import TypedDict

from strawberry.ext.dataclasses.dataclasses import dataclass_init_fn

if sys.version_info >= (3, 10):

    class DataclassArguments(TypedDict, total=False):
        init: bool
        repr: bool
        eq: bool
        order: bool
        unsafe_hash: bool
        frozen: bool
        match_args: bool
        kw_only: bool | _MISSING_TYPE
        slots: bool

else:

    class DataclassArguments(TypedDict, total=False):
        init: bool
        repr: bool
        eq: bool
        order: bool
        unsafe_hash: bool
        frozen: bool
        slots: bool


def add_custom_init_fn(cls: Any) -> None:
    fields = [
        f
        for f in getattr(cls, _FIELDS).values()
        if f._field_type in (_FIELD, _FIELD_INITVAR)
    ]
    globals_ = sys.modules[cls.__module__].__dict__

    _set_new_attribute(
        cls,
        "__init__",
        dataclass_init_fn(
            fields=fields,
            frozen=False,
            has_post_init=hasattr(cls, _POST_INIT_NAME),
            self_name="__dataclass_self__" if "self" in fields else "self",
            globals_=globals_,
        ),
    )

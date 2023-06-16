from __future__ import annotations

import sys
from dataclasses import (  # type: ignore
    _FIELD,
    _FIELD_INITVAR,
    _FIELDS,
    _POST_INIT_NAME,
    _set_new_attribute,
)
from typing import Any

from strawberry.ext.dataclasses.dataclasses import dataclass_init_fn


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

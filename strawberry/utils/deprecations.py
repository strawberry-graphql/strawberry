from __future__ import annotations

import warnings
from typing import Any, Optional


class DEPRECATION_MESSAGES:  # noqa: N801
    _TYPE_DEFINITION = (
        "_type_definition is deprecated, use __strawberry_definition__ instead"
    )


class DeprecatedDescriptor:
    def __init__(self, msg: str, alias: object, attr_name: str) -> None:
        self.msg = msg
        self.alias = alias
        self.attr_name = attr_name

    def warn(self) -> None:
        warnings.warn(self.msg, stacklevel=2)

    def __get__(self, obj: Optional[object], type: Optional[type] = None) -> Any:
        self.warn()
        return self.alias

    def inject(self, klass: type) -> None:
        setattr(klass, self.attr_name, self)


__all__ = ["DEPRECATION_MESSAGES", "DeprecatedDescriptor"]

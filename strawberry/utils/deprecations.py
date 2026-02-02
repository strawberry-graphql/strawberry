from __future__ import annotations

import warnings
from typing import Any


class DeprecatedDescriptor:
    """A descriptor that emits a deprecation warning when accessed.

    Used to create deprecated attribute aliases that point to new attributes.

    Example:
        >>> @strawberry.type
        ... class MyType:
        ...     __strawberry_definition__ = SomeDefinition()
        ...
        >>> DeprecatedDescriptor(
        ...     "_old_attr is deprecated, use __strawberry_definition__ instead",
        ...     MyType.__strawberry_definition__,
        ...     "_old_attr",
        ... ).inject(MyType)
        >>> # Now accessing MyType._old_attr will warn and return __strawberry_definition__
    """

    def __init__(self, msg: str, alias: object, attr_name: str) -> None:
        self.msg = msg
        self.alias = alias
        self.attr_name = attr_name

    def warn(self) -> None:
        warnings.warn(self.msg, stacklevel=2)

    def __get__(self, obj: object | None, type: type | None = None) -> Any:
        self.warn()
        return self.alias

    def inject(self, klass: type) -> None:
        setattr(klass, self.attr_name, self)


__all__ = ["DeprecatedDescriptor"]

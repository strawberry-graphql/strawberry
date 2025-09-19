import dataclasses
import sys
from typing import Any

from .field import StrawberryField


class StrawberryDataclassField(dataclasses.Field):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._strawberry_field: StrawberryField | None = kwargs.pop(
            "_strawberry_field", None
        )
        super().__init__(*args, **kwargs)

    @classmethod
    def from_strawberry_field(
        cls, field: StrawberryField
    ) -> "StrawberryDataclassField":
        is_basic_field = not field.base_resolver

        kwargs: dict[str, Any] = {}

        if sys.version_info >= (3, 10):
            kwargs["kw_only"] = dataclasses.MISSING

        return cls(
            default=field.default,
            default_factory=field.default_factory,  # type: ignore
            init=is_basic_field,
            repr=is_basic_field,
            compare=is_basic_field,
            hash=None,
            metadata=field.metadata or {},
            _strawberry_field=field,
            **kwargs,
        )

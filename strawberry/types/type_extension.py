from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator
    from dataclasses import Field

    from strawberry.types.base import StrawberryObjectDefinition


class TypeExtension:
    def on_wrap_dataclass(self, cls: type[Any]) -> Iterator[None]:
        """Called before and after strawberry wrapping process."""
        yield None

    def on_field(self, field: Field[Any]) -> Field[Any]:
        """Called for each field, _MUST_ return valid Field or StrawberryField."""
        return field

    def on_object_definition(
        self, object_definition: StrawberryObjectDefinition
    ) -> None:
        """Called after the object definition is created."""
        return


__all__ = ["TypeExtension"]

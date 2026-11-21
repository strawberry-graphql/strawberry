from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator
    from dataclasses import Field


class TypeExtension:
    def on_wrap_dataclass(
        self,
        cls: type[Any],
        name: str | None,
        is_input: bool,
        is_interface: bool,
    ) -> Iterator[None]:
        """Called before and after (containing StrwaberryObjectDefinition) strawberry wrapping process."""
        yield None

    def on_field(self, field: Field[Any]) -> Field[Any]:
        """Called for each field.

        Method _MUST_ return valid Field or StrawberryField.
        """
        return field


__all__ = ["TypeExtension"]

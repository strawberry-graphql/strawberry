from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strawberry.types.types import TypeDefinition


class TypeExtension:
    def apply(self, strawberry_type: TypeDefinition) -> None:  # pragma: no cover
        pass

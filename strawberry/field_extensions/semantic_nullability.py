from __future__ import annotations

from typing import TYPE_CHECKING, Any

from strawberry.exceptions.semantic_nullability import InvalidNullReturnError
from strawberry.extensions import FieldExtension

if TYPE_CHECKING:
    from strawberry.extensions.field_extension import (
        AsyncExtensionResolver,
        SyncExtensionResolver,
    )
    from strawberry.types import Info


class SemanticNonNullExtension(FieldExtension):
    def resolve(
        self, next_: SyncExtensionResolver, source: Any, info: Info, **kwargs: Any
    ) -> Any:
        resolved = next_(source, info, **kwargs)
        if resolved is not None:
            return resolved
        else:
            raise InvalidNullReturnError()

    async def resolve_async(
        self, next_: AsyncExtensionResolver, source: Any, info: Info, **kwargs: Any
    ) -> Any:
        resolved = await next_(source, info, **kwargs)
        if resolved is not None:
            return resolved
        else:
            raise InvalidNullReturnError()

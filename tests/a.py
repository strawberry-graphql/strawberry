from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

import strawberry

if TYPE_CHECKING:
    from tests.b import B


@strawberry.type
class A:
    id: strawberry.ID

    @strawberry.field
    async def b(self) -> Annotated[B, strawberry.lazy("tests.b")]:
        from tests.b import B

        return B(id=self.id)

    @strawberry.field
    async def optional_b(self) -> Annotated[B, strawberry.lazy("tests.b")] | None:
        from tests.b import B

        return B(id=self.id)

    @strawberry.field
    async def optional_b2(self) -> Optional[Annotated[B, strawberry.lazy("tests.b")]]:
        from tests.b import B

        return B(id=self.id)

from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import Annotated

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

from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import Annotated

import strawberry

if TYPE_CHECKING:
    from tests.a import A


@strawberry.type
class B:
    id: strawberry.ID

    @strawberry.field
    async def a(self) -> Annotated[A, strawberry.lazy("tests.a"), object()]:
        from tests.a import A

        return A(id=self.id)

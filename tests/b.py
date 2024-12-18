from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

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

    @strawberry.field
    async def a_list(
        self,
    ) -> list[Annotated[A, strawberry.lazy("tests.a")]]:  # pragma: no cover
        from tests.a import A

        return [A(id=self.id)]

    @strawberry.field
    async def optional_a(
        self,
    ) -> Annotated[A, strawberry.lazy("tests.a"), object()] | None:
        from tests.a import A

        return A(id=self.id)

    @strawberry.field
    async def optional_a2(
        self,
    ) -> Optional[Annotated[A, strawberry.lazy("tests.a"), object()]]:
        from tests.a import A

        return A(id=self.id)

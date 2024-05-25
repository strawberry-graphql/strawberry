from __future__ import annotations

from typing import TYPE_CHECKING, List
from typing_extensions import Annotated

import strawberry

if TYPE_CHECKING:
    from tests.c import C


@strawberry.type
class D:
    id: strawberry.ID

    @strawberry.field
    async def c_list(
        self,
    ) -> List[Annotated[C, strawberry.lazy("tests.c")]]:  # pragma: no cover
        from tests.c import C

        return [C(id=self.id)]

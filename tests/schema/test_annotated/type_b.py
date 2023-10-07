from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated
from uuid import UUID

import strawberry
from strawberry.types import Info


@strawberry.type
class Query:
    @strawberry.field
    def get_testing(
        self,
        id_: Annotated[UUID, strawberry.argument(name="id")],
        info: Info[None, None],
    ) -> Optional[str]:
        ...

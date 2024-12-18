from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def get_testing(
        self,
        id_: Annotated[UUID, strawberry.argument(name="id")],
        info: strawberry.Info,
    ) -> Optional[str]: ...

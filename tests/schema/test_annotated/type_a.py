from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated
from uuid import UUID

import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def get_testing(
        self,
        info: strawberry.Info,
        id_: Annotated[UUID, strawberry.argument(name="id")],
    ) -> Optional[str]: ...

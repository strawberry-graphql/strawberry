# With `from __future__ import annotations`, pydantic can't resolve the
# annotations, and Strawberry reads `strawberry.lazy()` when it resolves them
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import pydantic

import strawberry

if TYPE_CHECKING:
    from .account import Account


@strawberry.pydantic.type
class Owner(pydantic.BaseModel):
    name: str
    account: Annotated[Account, strawberry.lazy("tests.pydantic.lazy.account")]
    accounts: list[
        Annotated[Account, strawberry.lazy("tests.pydantic.lazy.account")]
    ] = []

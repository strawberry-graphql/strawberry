# Without `from __future__ import annotations`, so that pydantic reads the
# `strawberry.field()` of a type that's only imported for type checking
from typing import TYPE_CHECKING, Annotated, Any

import pydantic

import strawberry

if TYPE_CHECKING:
    from .account import Account


class IsAdmin(strawberry.BasePermission):
    message = "Admins only"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return False


@strawberry.pydantic.type
class Owner(pydantic.BaseModel):
    name: str
    account: Annotated[
        "Account",
        strawberry.lazy("tests.pydantic.lazy.account"),
        strawberry.field(permission_classes=[IsAdmin]),
    ]

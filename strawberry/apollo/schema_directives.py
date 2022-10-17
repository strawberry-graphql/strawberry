from enum import Enum
from typing import Optional

from strawberry.enum import enum
from strawberry.schema_directive import Location, schema_directive
from strawberry.unset import UNSET


@enum
class CacheControlScope(Enum):
    PRIVATE = 0
    PUBLIC = 1


@schema_directive(
    name="cacheControl",
    locations=[
        Location.FIELD_DEFINITION,
        Location.OBJECT,
        Location.INTERFACE,
        Location.UNION,
    ],
)
class CacheControl:
    max_age: Optional[int]
    scope: Optional[CacheControlScope]
    inheredit_max_age: Optional[bool]

    def __init__(
        self,
        *,
        max_age: Optional[int] = UNSET,
        scope: Optional[CacheControlScope] = UNSET,
        inheredit_max_age: Optional[bool] = UNSET
    ):
        self.max_age = max_age
        self.scope = scope
        self.inheredit_max_age = inheredit_max_age

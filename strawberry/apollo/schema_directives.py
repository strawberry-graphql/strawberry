from enum import Enum
from typing import Optional

from strawberry.enum import enum
from strawberry.schema_directive import Location, schema_directive


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
    scope: Optional[CacheControlScope] = CacheControlScope.PUBLIC
    inheredit_max_age: Optional[bool] = False


__all__ = ["CacheControl"]

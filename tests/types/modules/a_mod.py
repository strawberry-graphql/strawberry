from typing import List

import strawberry


def a_resolver() -> List["AObject"]:
    return []


@strawberry.type
class ABase:
    a_name: str


@strawberry.type
class AObject(ABase):
    a_age: int

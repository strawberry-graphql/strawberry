from typing import List

import strawberry


def b_resolver() -> List["BObject"]:
    return []


@strawberry.type
class BBase:
    b_name: str


@strawberry.type
class BObject(BBase):
    b_age: int

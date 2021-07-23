from typing import Optional

import strawberry


def test_inherited_fields():
    @strawberry.type
    class A:
        a: str = strawberry.field(default="")

    @strawberry.type
    class B(A):
        b: Optional[str] = strawberry.field(default=None)

    assert strawberry.Schema(query=B)

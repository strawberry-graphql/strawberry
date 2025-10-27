import strawberry


def test_inherited_fields():
    @strawberry.type
    class A:
        a: str = strawberry.field(default="")

    @strawberry.type
    class B(A):
        b: str | None = strawberry.field(default=None)

    assert strawberry.Schema(query=B)

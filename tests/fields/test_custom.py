import strawberry
from strawberry.field import StrawberryField


strawberry.field


def test_override_get_result():
    class WorldField(StrawberryField):
        def get_result(self, *args, **kwargs):
            res = super().get_result(args, **kwargs)
            return res + " world"

    def resolve_hello(self) -> str:
        return "hello"

    @strawberry.type
    class Query:
        hello: str = WorldField.evolve_with_resolver(resolve_hello)

    schema = strawberry.Schema(query=Query)
    res = schema.execute_sync("{hello}").data
    assert res["hello"] == "hello world"

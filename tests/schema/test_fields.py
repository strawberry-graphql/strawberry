import strawberry
from strawberry.field import StrawberryField


def test_custom_field():
    class CustomField(StrawberryField):
        def get_result(self, root, info, args, kwargs):
            return getattr(root, self.python_name) * 2

    @strawberry.type
    class Query:
        a: str = CustomField(default="Example")  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = "{ a }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data == {"a": "ExampleExample"}

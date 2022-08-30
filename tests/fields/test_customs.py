import strawberry
from strawberry.field import StrawberryField
from strawberry.types.types import get_type_definition


def test_basic_override_get_result():
    class HelloField(StrawberryField):
        def get_result(self, *args, **kwargs):
            res = super().get_result(*args, **kwargs)
            return "hello " + res

    @strawberry.type
    class Query:
        @HelloField()
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        query="""
        {hello}
    """
    )
    assert not result.errors
    assert result.data["hello"] == "hello world"


def test_batched_fields():
    class HelloField(StrawberryField):
        def get_result(self, *args, **kwargs):
            res = super().get_result(*args, **kwargs)
            return "hello " + res

    class FooField(StrawberryField):
        def get_result(self, *args, **kwargs):
            res = super().get_result(*args, **kwargs)
            return "foo " + res

    @strawberry.type
    class Query:
        @HelloField()
        @FooField()
        def hello(self) -> str:
            return "world"

    definition = get_type_definition(Query)
    assert isinstance(definition.fields[0], FooField)
    assert isinstance(definition.fields[0], HelloField)
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        query="""
        {hello}
    """
    )
    assert not result.errors
    assert result.data["hello"] == "hello world"

import dataclasses
from operator import getitem

import strawberry
from strawberry.field import StrawberryField
from strawberry.schema.config import StrawberryConfig


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


def test_default_resolver_gets_attribute():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Patrick")

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["user"]["name"] == "Patrick"


def test_can_change_default_resolver():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return {"name": "Patrick"}  # type: ignore

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(default_resolver=getitem),
    )

    query = "{ user { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["user"]["name"] == "Patrick"


def test_field_metadata():
    @strawberry.type
    class Query:
        a: str = strawberry.field(default="Example", metadata={"Foo": "Bar"})

    (a,) = dataclasses.fields(Query)
    assert a.metadata == {"Foo": "Bar"}

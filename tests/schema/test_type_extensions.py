import textwrap
from typing import Annotated

import pytest

import strawberry
from strawberry.printer import print_schema
from strawberry.schema_directive import Location


def test_object_extension_can_extend_existing_type():
    @strawberry.type(name="User")
    class User:
        name: str

    @strawberry.type(name="User", extend=True)
    class UserExtension:
        @strawberry.field
        def extra(self) -> str:
            return self.extra

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            user = User(name="Ada")
            user.extra = "Lovelace"
            return user

    schema = strawberry.Schema(query=Query, types=[UserExtension])

    expected = """
    type Query {
      user: User!
    }

    type User {
      name: String!
    }

    extend type User {
      extra: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()

    result = schema.execute_sync("{ user { name extra } }")

    assert not result.errors
    assert result.data == {"user": {"name": "Ada", "extra": "Lovelace"}}


def test_object_extension_registered_before_base_preserves_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type(name="User")
    class User(Node):
        name: str

    @strawberry.type(name="User", extend=True)
    class UserExtension:
        @strawberry.field
        def extra(self) -> str:
            return self.extra

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserExtension:
            user = User(id=strawberry.ID("1"), name="Ada")
            user.extra = "Lovelace"
            return user

    schema = strawberry.Schema(query=Query, types=[User])
    graphql_user_type = schema._schema.get_type("User")

    assert graphql_user_type is not None
    assert [interface.name for interface in graphql_user_type.interfaces] == ["Node"]

    result = schema.execute_sync("{ user { id name extra } }")

    assert not result.errors
    assert result.data == {"user": {"id": "1", "name": "Ada", "extra": "Lovelace"}}


def test_object_extension_rejects_duplicate_fields():
    @strawberry.type(name="User")
    class User:
        name: str

    @strawberry.type(name="User", extend=True)
    class UserExtension:
        name: str

    @strawberry.type
    class Query:
        user: User

    with pytest.raises(
        TypeError,
        match="Type User defines duplicate extension field\\(s\\): name",
    ):
        strawberry.Schema(query=Query, types=[UserExtension])


def test_extend_type_reachable_twice_does_not_extend_itself():
    @strawberry.type(name="Product", extend=True)
    class Product:
        upc: str

    @strawberry.type
    class Review:
        product: Product

    @strawberry.type
    class Query:
        @strawberry.field
        def review(self) -> Review: ...

        @strawberry.field
        def product(self) -> Product: ...

    schema = strawberry.Schema(query=Query)

    expected = """
    extend type Product {
      upc: String!
    }

    type Query {
      review: Review!
      product: Product!
    }

    type Review {
      product: Product!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()


@pytest.mark.parametrize("is_input", [False, True])
def test_extension_directives_are_available_to_introspection(is_input):
    @strawberry.schema_directive(locations=[Location.OBJECT, Location.INPUT_OBJECT])
    class ExtensionType: ...

    @strawberry.schema_directive(
        locations=[Location.FIELD_DEFINITION, Location.INPUT_FIELD_DEFINITION]
    )
    class ExtensionField: ...

    decorator = strawberry.input if is_input else strawberry.type

    @decorator(name="Item")
    class Item:
        name: str

    @decorator(name="Item", extend=True, directives=[ExtensionType()])
    class ItemExtension:
        extra: Annotated[str, strawberry.field(directives=[ExtensionField()])]

    if is_input:

        @strawberry.type
        class Query:
            @strawberry.field
            def item(self, value: Item) -> str:
                return value.name

    else:

        @strawberry.type
        class Query:
            item: Item

    schema = strawberry.Schema(query=Query, types=[ItemExtension])
    result = schema.execute_sync("{ __schema { directives { name } } }")

    assert result.errors is None
    names = [directive["name"] for directive in result.data["__schema"]["directives"]]
    assert names.count("extensionType") == 1
    assert names.count("extensionField") == 1

    sdl = print_schema(schema)
    keyword = "input" if is_input else "type"
    assert f"extend {keyword} Item @extensionType" in sdl
    assert "extra: String! @extensionField" in sdl

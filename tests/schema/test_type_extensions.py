import textwrap
from typing import Annotated

import pytest
from graphql import build_schema

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


@pytest.mark.parametrize("is_input", [False, True])
@pytest.mark.parametrize("extension_first", [False, True])
@pytest.mark.parametrize("directive_on_base", [False, True])
@pytest.mark.parametrize("repeatable", [False, True])
def test_composed_type_directives_respect_repeatability(
    is_input, extension_first, directive_on_base, repeatable
):
    @strawberry.schema_directive(
        name="markerPolicy",
        locations=[Location.OBJECT, Location.INPUT_OBJECT],
        repeatable=repeatable,
    )
    class Marker: ...

    decorator = strawberry.input if is_input else strawberry.type

    @decorator(name="Item", directives=[Marker()] if directive_on_base else [])
    class Item:
        name: str

    @decorator(name="Item", extend=True, directives=[Marker()])
    class ItemExtension:
        extra: str

    @decorator(name="Item", extend=True, directives=[Marker()])
    class OtherExtension:
        other: str

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

    types = [Item, ItemExtension]
    if not directive_on_base:
        types.append(OtherExtension)
    if extension_first:
        types.reverse()

    if not repeatable:
        with pytest.raises(
            ValueError,
            match="Type 'Item' repeats non-repeatable directive '@markerPolicy'",
        ):
            strawberry.Schema(query=Query, types=types)
        return

    schema = strawberry.Schema(query=Query, types=types)
    sdl = schema.as_str()
    assert sdl.count(" @markerPolicy") == 3  # Definition and two applications.
    build_schema(sdl)


@pytest.mark.parametrize("reverse_order", [False, True])
def test_federation_extensions_compose_without_local_base(reverse_order):
    @strawberry.federation.type(name="Item", extend=True)
    class FirstExtension:
        name: str

    @strawberry.federation.type(name="Item", extend=True)
    class SecondExtension:
        @strawberry.field
        def extra(self) -> str:
            return "extra"

    @strawberry.type
    class Query:
        @strawberry.field
        def item(self) -> FirstExtension:
            return FirstExtension(name="item")

    types = [FirstExtension, SecondExtension]
    if reverse_order:
        types.reverse()
    schema = strawberry.federation.Schema(query=Query, types=types)

    result = schema.execute_sync("{ item { name extra } }")
    assert result.errors is None
    assert result.data == {"item": {"name": "item", "extra": "extra"}}
    sdl = schema.as_str()
    assert sdl.count("extend type Item") == 2
    assert "\ntype Item" not in sdl

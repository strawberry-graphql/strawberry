"""Tests for input types that build their own value with `from_input`."""

from typing import Any

import strawberry
from strawberry.directive import DirectiveLocation, DirectiveValue
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.federation.schema_directives import Key
from strawberry.types.arguments import InputContext
from strawberry.types.base import get_object_definition
from strawberry.types.info import Info


def _record_calls(cls: type, calls: list[InputContext]) -> None:
    def from_input(cls: type, value: Any, context: InputContext) -> Any:
        calls.append(context)

        return cls(**{key.lower(): item for key, item in value.items()})

    get_object_definition(cls, strict=True).from_input = from_input


def test_field_arguments_are_built_with_the_info():
    @strawberry.input
    class Filter:
        query: str

    calls: list[InputContext] = []
    _record_calls(Filter, calls)

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: Filter) -> str:
            return filter.query

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ search(filter: { query: "jam" }) }')

    assert not result.errors
    assert result.data == {"search": "jam"}

    [context] = calls

    assert isinstance(context.info, Info)
    assert context.info.field_name == "search"
    assert context.path == ("filter",)


def test_directive_arguments_are_built_with_the_info():
    @strawberry.input
    class Options:
        suffix: str

    calls: list[InputContext] = []
    _record_calls(Options, calls)

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def decorate(value: DirectiveValue[str], options: Options) -> str:
        return value + options.suffix

    @strawberry.type
    class Query:
        @strawberry.field
        def name(self) -> str:
            return "jam"

    schema = strawberry.Schema(query=Query, directives=[decorate])

    result = schema.execute_sync('{ name @decorate(options: { suffix: "!" }) }')

    assert not result.errors
    assert result.data == {"name": "jam!"}

    [context] = calls

    assert isinstance(context.info, Info)
    assert context.info.field_name == "name"
    assert context.path == ("options",)


def test_federation_entities_are_built_with_the_info():
    @strawberry.federation.type(directives=[Key(fields="id")])
    class Product:
        id: strawberry.ID

    calls: list[InputContext] = []
    _record_calls(Product, calls)

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self) -> Product:
            return Product(id=strawberry.ID("1"))

    schema = strawberry.federation.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            _entities(representations: [{ __typename: "Product", id: "1" }]) {
                ... on Product { id }
            }
        }
        """
    )

    assert not result.errors
    assert result.data == {"_entities": [{"id": "1"}]}

    [context] = calls

    assert isinstance(context.info, Info)
    assert context.info.field_name == "_entities"


def test_input_instances_given_as_defaults_are_built_with_the_hook():
    @strawberry.input
    class Filter:
        query: str

    calls: list[InputContext] = []
    _record_calls(Filter, calls)

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: Filter = Filter(query="jam")) -> str:
            return filter.query

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ search }")

    assert not result.errors
    assert result.data == {"search": "jam"}

    # the default is converted to an input value, like values sent by clients
    [context] = calls

    assert context.path == ("filter",)


def test_inputs_converted_by_a_hook_know_their_location():
    @strawberry.input
    class Item:
        name: str

    @strawberry.input
    class Order:
        items: list[Item]

    item_paths: list[tuple[str | int, ...]] = []

    def build_item(cls: type, value: Any, context: InputContext) -> Any:
        item_paths.append(context.path)

        return cls(name=value["name"])

    def build_order(cls: type, value: Any, context: InputContext) -> Any:
        return cls(
            items=[
                context.convert(item, Item, "items", index)
                for index, item in enumerate(value["items"])
            ]
        )

    get_object_definition(Item, strict=True).from_input = build_item
    get_object_definition(Order, strict=True).from_input = build_order

    @strawberry.type
    class Query:
        @strawberry.field
        def count(self, order: Order) -> int:
            return len(order.items)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        '{ count(order: { items: [{ name: "a" }, { name: "b" }] }) }'
    )

    assert not result.errors
    assert result.data == {"count": 2}
    assert item_paths == [("order", "items", 0), ("order", "items", 1)]


def test_federation_entities_know_their_location_and_keep_their_errors():
    @strawberry.federation.type(directives=[Key(fields="id")])
    class Product:
        id: strawberry.ID

    paths: list[tuple[str | int, ...]] = []

    def build_product(cls: type, value: Any, context: InputContext) -> Any:
        paths.append(context.path)

        if value["id"] == "invalid":
            raise StrawberryGraphQLError("The product id is invalid")

        return cls(id=value["id"])

    get_object_definition(Product, strict=True).from_input = build_product

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self) -> Product:
            return Product(id=strawberry.ID("1"))

    schema = strawberry.federation.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            _entities(representations: [
                { __typename: "Product", id: "1" },
                { __typename: "Product", id: "invalid" }
            ]) {
                ... on Product { id }
            }
        }
        """
    )

    assert paths == [("representations", 0), ("representations", 1)]
    assert result.data == {"_entities": [{"id": "1"}, None]}
    assert result.errors
    assert result.errors[0].message == "The product id is invalid"


def test_convert_accepts_python_annotations():
    @strawberry.input
    class Item:
        name: str

    @strawberry.input
    class Order:
        items: list[Item]
        note: str | None = None

    def build_order(cls: type, value: Any, context: InputContext) -> Any:
        return cls(
            items=context.convert(value["items"], list[Item], "items"),
            note=context.convert(value["note"], str | None, "note"),
        )

    get_object_definition(Order, strict=True).from_input = build_order

    @strawberry.type
    class Query:
        @strawberry.field
        def names(self, order: Order) -> list[str]:
            return [item.name for item in order.items]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync('{ names(order: { items: [{ name: "a" }] }) }')

    assert not result.errors
    assert result.data == {"names": ["a"]}

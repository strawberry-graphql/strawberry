"""Tests for input types that build their own value with `from_input`."""

from typing import Any

import strawberry
from strawberry.directive import DirectiveLocation, DirectiveValue
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

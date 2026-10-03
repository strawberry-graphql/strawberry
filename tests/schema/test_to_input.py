"""Tests for input types that choose their fields with `to_input`."""

from collections.abc import Mapping
from typing import Any, Generic, TypeVar

import strawberry
from strawberry.types.arguments import InputContext
from strawberry.types.base import get_object_definition

INTROSPECTION_QUERY = """
{
    __type(name: "Query") {
        fields { args { defaultValue } }
    }
}
"""


def _query_default(schema: strawberry.Schema) -> str:
    result = schema.execute_sync(INTROSPECTION_QUERY)

    assert not result.errors
    assert result.data

    return result.data["__type"]["fields"][0]["args"][0]["defaultValue"]


def test_to_input_chooses_the_fields_of_a_default():
    @strawberry.input
    class Filter:
        limit: int = 10
        query: str | None = "all"
        explicit: list[str] = strawberry.field(default_factory=list)

    def to_input(filter: Filter) -> dict[str, Any]:
        # e.g. only the fields that were set when the instance was created
        return {"limit": filter.limit}

    get_object_definition(Filter, strict=True).to_input = to_input

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: Filter = Filter(limit=5, query=None)) -> str:
            return f"{filter.limit} {filter.query} {filter.explicit}"

    schema = strawberry.Schema(query=Query)

    assert "search(filter: Filter! = { limit: 5 }): String!" in str(schema)
    assert _query_default(schema) == "{ limit: 5 }"

    result = schema.execute_sync("{ search }")

    # the fields that were left out get their default
    assert not result.errors
    assert result.data == {"search": "5 all []"}


def test_to_input_uses_python_names():
    @strawberry.input
    class Pagination:
        page_size: int = 10
        # its GraphQL name is the python name of another field
        offset: int = strawberry.field(default=0, name="cursor")
        cursor: str = strawberry.field(default="start", name="after")

    get_object_definition(Pagination, strict=True).to_input = lambda pagination: {
        "page_size": pagination.page_size,
        "cursor": pagination.cursor,
    }

    @strawberry.type
    class Query:
        @strawberry.field
        def items(
            self,
            pagination: Pagination = Pagination(page_size=5, offset=3, cursor="custom"),
        ) -> str:
            return f"{pagination.page_size} {pagination.offset} {pagination.cursor}"

    schema = strawberry.Schema(query=Query)

    assert _query_default(schema) == '{ pageSize: 5, after: "custom" }'
    assert schema.execute_sync("{ items }").data == {"items": "5 0 custom"}


def test_to_input_is_used_for_nested_instances_and_input_field_defaults():
    @strawberry.input
    class Pagination:
        limit: int = 10
        offset: int = 0

    get_object_definition(Pagination, strict=True).to_input = lambda pagination: {
        "limit": pagination.limit
    }

    @strawberry.input
    class Filter:
        query: str = ""
        pagination: Pagination = strawberry.field(
            default_factory=lambda: Pagination(limit=3, offset=1)
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def search(
            self, filter: Filter = Filter(query="jam", pagination=Pagination(limit=5))
        ) -> str:
            return (
                f"{filter.query} {filter.pagination.limit} {filter.pagination.offset}"
            )

    schema = strawberry.Schema(query=Query)

    sdl = str(schema)

    assert "pagination: Pagination! = { limit: 3 }" in sdl
    assert 'filter: Filter! = { query: "jam", pagination: { limit: 5 } }' in sdl

    result = schema.execute_sync(
        '{ default: search other: search(filter: { query: "x" }) }'
    )

    assert not result.errors
    # offset is left out by `to_input`, so it gets its default
    assert result.data == {"default": "jam 5 0", "other": "x 3 0"}


def test_to_input_is_kept_for_generic_specializations():
    T = TypeVar("T")

    @strawberry.input
    class Page(Generic[T]):
        after: T | None = None
        limit: int = 10

    get_object_definition(Page, strict=True).to_input = lambda page: {
        "limit": page.limit
    }

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self, page: Page[int] = Page(after=3, limit=5)) -> str:
            return f"{page.after} {page.limit}"

    schema = strawberry.Schema(query=Query)

    assert _query_default(schema) == "{ limit: 5 }"
    assert schema.execute_sync("{ items }").data == {"items": "None 5"}


def test_none_returned_by_to_input_is_an_explicit_null():
    @strawberry.input
    class Patch:
        name: strawberry.Maybe[str | None]
        bio: strawberry.Maybe[str | None]

    get_object_definition(Patch, strict=True).to_input = lambda patch: {"name": None}

    @strawberry.type
    class Query:
        @strawberry.field
        def update(self, patch: Patch = Patch(name=None, bio=None)) -> str:
            return f"{patch.name} {patch.bio}"

    schema = strawberry.Schema(query=Query)

    assert _query_default(schema) == "{ name: null }"
    assert schema.execute_sync("{ update }").data == {"update": "Some(None) None"}


def test_fields_left_out_by_to_input_are_not_passed_to_from_input():
    received: list[dict[str, Any]] = []

    @strawberry.input
    class Patch:
        name: str | None = None
        role: str = "user"

    def build(cls: type, value: Mapping[str, Any], context: InputContext) -> Any:
        received.append(dict(value))

        return cls(**value)

    definition = get_object_definition(Patch, strict=True)
    definition.from_input = build
    definition.to_input = lambda patch: {"name": patch.name}

    @strawberry.type
    class Query:
        @strawberry.field
        def update(self, patch: Patch = Patch(name="Ada")) -> str:
            return f"{patch.name} {patch.role}"

    schema = strawberry.Schema(query=Query)

    assert 'role: String! = "user"' in str(schema)

    # GraphQL only fills in the published defaults of values sent by clients
    assert schema.execute_sync("{ update }").data == {"update": "Ada user"}
    assert schema.execute_sync('{ update(patch: { name: "Ada" }) }').data == {
        "update": "Ada user"
    }
    assert received == [{"name": "Ada"}, {"name": "Ada", "role": "user"}]

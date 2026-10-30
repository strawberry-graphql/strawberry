from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Generic, Optional, TypeVar, Union

import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.relay import GlobalID, to_base64

if TYPE_CHECKING:
    from tests.relay.lazy_global_id_types import LazyBook
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Book:
    id: GlobalID
    title: str
    debug: str


@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> list[Book]:
        return []

    @strawberry.field
    def book(self, id: GlobalID) -> Book | None:
        return Book(id=id, title="Title", debug=str(type(id)))


def test_uses_id_by_default() -> None:
    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Book {
  id: ID!
  title: String!
  debug: String!
}

type Query {
  books: [Book!]!
  book(id: ID!): Book
}\
""")

    result = schema.execute_sync('query { book(id: "Qm9vazox") { id, debug } }')

    assert result.errors is None
    assert result.data == snapshot(
        {
            "book": {
                "id": "Qm9vazox",
                "debug": "<class 'strawberry.relay.types.GlobalID'>",
            }
        }
    )


def test_we_can_still_use_global_id() -> None:
    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(relay_use_legacy_global_id=True)
    )

    assert str(schema) == snapshot('''\
type Book {
  id: GlobalID!
  title: String!
  debug: String!
}

"""
The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID.
"""
scalar GlobalID @specifiedBy(url: "https://relay.dev/graphql/objectidentification.htm")

type Query {
  books: [Book!]!
  book(id: GlobalID!): Book
}\
''')

    result = schema.execute_sync('query { book(id: "Qm9vazox") { id, debug } }')

    assert result.errors is None
    assert result.data == snapshot(
        {
            "book": {
                "id": "Qm9vazox",
                "debug": "<class 'strawberry.relay.types.GlobalID'>",
            }
        }
    )


def test_can_use_both_global_id_and_id() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, id: GlobalID) -> str:
            return id.node_id

        @strawberry.field
        def hello2(self, id: strawberry.ID) -> str:
            return id

    schema = strawberry.Schema(Query)

    assert str(schema) == snapshot("""\
type Query {
  hello(id: ID!): String!
  hello2(id: ID!): String!
}\
""")

    result = schema.execute_sync(
        """
        query ($globalId: ID!, $id: ID!) {
            a: hello(id: "Qm9vazox")
            b: hello2(id: "1")
            c: hello(id: $globalId)
            d: hello2(id: $id)
        }
        """,
        variable_values={"globalId": "Qm9vazox", "id": "1"},
    )

    assert result.errors is None
    assert result.data == snapshot(
        {
            "a": "1",
            "b": "1",
            "c": "1",
            "d": "1",
        }
    )


def test_can_use_both_global_id_and_id_legacy() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, id: GlobalID) -> str:
            return id.node_id

        @strawberry.field
        def hello2(self, id: strawberry.ID) -> str:
            return id

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(relay_use_legacy_global_id=True)
    )

    assert str(schema) == snapshot('''\
"""
The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID.
"""
scalar GlobalID @specifiedBy(url: "https://relay.dev/graphql/objectidentification.htm")

type Query {
  hello(id: GlobalID!): String!
  hello2(id: ID!): String!
}\
''')

    result = schema.execute_sync(
        """
        query ($globalId: GlobalID!, $id: ID!) {
            a: hello(id: $globalId)
            b: hello2(id: $id)
            c: hello(id: "Qm9vazox")
            d: hello2(id: "1")
        }
        """,
        variable_values={"globalId": "Qm9vazox", "id": "1"},
    )

    assert result.errors is None
    assert result.data == snapshot(
        {
            "a": "1",
            "b": "1",
            "c": "1",
            "d": "1",
        }
    )


def test_can_return_id() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, id: GlobalID) -> GlobalID:
            return id

        @strawberry.field
        def hello2(self, id: strawberry.ID) -> strawberry.ID:
            return id

    schema = strawberry.Schema(Query)

    result = schema.execute_sync(
        """
        query ($globalId: ID!, $id: ID!) {
            a: hello(id: "Qm9vazox")
            b: hello2(id: "1")
            c: hello(id: $globalId)
            d: hello2(id: $id)
        }
        """,
        variable_values={"globalId": "Qm9vazox", "id": "1"},
    )

    assert result.errors is None
    assert result.data == snapshot(
        {
            "a": "Qm9vazox",
            "b": "1",
            "c": "Qm9vazox",
            "d": "1",
        }
    )


def test_can_return_global_id_legacy() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, id: GlobalID) -> GlobalID:
            return id

        @strawberry.field
        def hello2(self, id: strawberry.ID) -> strawberry.ID:
            return id

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(relay_use_legacy_global_id=True)
    )

    result = schema.execute_sync(
        """
        query ($globalId: GlobalID!, $id: ID!) {
            a: hello(id: $globalId)
            b: hello2(id: $id)
            c: hello(id: "Qm9vazox")
            d: hello2(id: "1")
        }
        """,
        variable_values={"globalId": "Qm9vazox", "id": "1"},
    )

    assert result.errors is None
    assert result.data == snapshot(
        {
            "a": "Qm9vazox",
            "b": "1",
            "c": "Qm9vazox",
            "d": "1",
        }
    )


@strawberry.type
class Team:
    id: GlobalID
    name: str


@strawberry.interface
class SomeInterface:
    id: strawberry.ID


class PlainClass:
    pass


T = TypeVar("T")


@strawberry.type
class GenericBox(Generic[T]):
    v: T


@strawberry.input
class GlobalIDInput:
    id: Annotated[GlobalID, Book]


@strawberry.input
class GlobalIDNestedInput:
    ids: list[Annotated[GlobalID, Book]]


def test_global_id_with_expected_type_accepts_matching_type() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def book(self, id: Annotated[GlobalID, Book]) -> str:
            return f"{id.type_name}:{id.node_id}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        f'{{ book(id: "{to_base64("Book", "1")}") }}',
    )

    assert not result.errors
    assert result.data == {"book": "Book:1"}


def test_global_id_with_expected_type_rejects_other_type() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def book(self, id: Annotated[GlobalID, Book]) -> str:
            return f"{id.type_name}:{id.node_id}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        f'{{ book(id: "{to_base64("Team", "1")}") }}',
    )

    assert result.errors
    assert (
        result.errors[0].message
        == 'GlobalID type "Team" does not match expected type "Book".'
    )


def test_global_id_with_expected_types_accepts_union() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def node(self, id: Annotated[GlobalID, Book, Team]) -> str:
            return f"{id.type_name}:{id.node_id}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        f'{{ a: node(id: "{to_base64("Book", "1")}") }}',
    )
    assert not result.errors
    assert result.data == {"a": "Book:1"}

    result = schema.execute_sync(
        f'{{ b: node(id: "{to_base64("Team", "2")}") }}',
    )
    assert not result.errors
    assert result.data == {"b": "Team:2"}

    result = schema.execute_sync(
        f'{{ c: node(id: "{to_base64("Other", "3")}") }}',
    )
    assert result.errors
    assert (
        result.errors[0].message
        == 'GlobalID type "Other" does not match expected type "Book" or "Team".'
    )


def test_global_id_with_expected_type_optional_allows_null() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def book(self, id: Annotated[Optional[GlobalID], Book]) -> str:
            if id is None:
                return "none"
            return f"{id.type_name}:{id.node_id}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ book(id: null) }")
    assert not result.errors
    assert result.data == {"book": "none"}

    result = schema.execute_sync(f'{{ book(id: "{to_base64("Team", "1")}") }}')
    assert result.errors

    # the nested Optional[Annotated[GlobalID, Book]] form is validated too
    @strawberry.type
    class NestedQuery:
        @strawberry.field
        def nested(self, id: Optional[Annotated[GlobalID, Book]] = None) -> str:
            if id is None:
                return "none"
            return f"{id.type_name}:{id.node_id}"

    nested_schema = strawberry.Schema(query=NestedQuery)

    result = nested_schema.execute_sync("{ nested(id: null) }")
    assert not result.errors
    assert result.data == {"nested": "none"}

    result = nested_schema.execute_sync(f'{{ nested(id: "{to_base64("Book", "1")}") }}')
    assert not result.errors
    assert result.data == {"nested": "Book:1"}

    result = nested_schema.execute_sync(f'{{ nested(id: "{to_base64("Team", "1")}") }}')
    assert result.errors


def test_global_id_without_expected_type_is_unaffected() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def node(self, id: GlobalID) -> str:
            return f"{id.type_name}:{id.node_id}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        f'{{ node(id: "{to_base64("Anything", "9")}") }}',
    )

    assert not result.errors
    assert result.data == {"node": "Anything:9"}


def test_global_id_with_union_of_expected_types() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def node(self, id: Annotated[GlobalID, Book | Team]) -> str:
            return f"{id.type_name}:{id.node_id}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(f'{{ a: node(id: "{to_base64("Book", "1")}") }}')
    assert not result.errors
    assert result.data == {"a": "Book:1"}

    result = schema.execute_sync(f'{{ b: node(id: "{to_base64("Team", "2")}") }}')
    assert not result.errors
    assert result.data == {"b": "Team:2"}

    result = schema.execute_sync(f'{{ c: node(id: "{to_base64("Other", "3")}") }}')
    assert result.errors
    assert (
        result.errors[0].message
        == 'GlobalID type "Other" does not match expected type "Book" or "Team".'
    )


def test_global_id_expected_type_must_not_be_an_interface() -> None:
    with pytest.raises(TypeError, match="is an interface"):

        @strawberry.type
        class Query:
            @strawberry.field
            def node(self, id: Annotated[GlobalID, SomeInterface]) -> str:
                return ""


def test_global_id_expected_type_must_be_a_strawberry_type() -> None:
    with pytest.raises(TypeError, match="must be strawberry types"):

        @strawberry.type
        class Query:
            @strawberry.field
            def book(self, id: Annotated[GlobalID, PlainClass]) -> str:  # type: ignore[type-arg]
                return ""


def test_global_id_expected_types_not_supported_on_list_items() -> None:
    with pytest.raises(TypeError, match="only supported directly on an argument"):

        @strawberry.type
        class Query:
            @strawberry.field
            def books(self, ids: list[Annotated[GlobalID, Book]]) -> str:
                return ""


def test_global_id_with_lazy_expected_type() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def book(
            self,
            id: Annotated[
                GlobalID,
                Annotated[
                    "LazyBook",  # noqa: UP037
                    strawberry.lazy("tests.relay.lazy_global_id_types"),
                ],
            ],
        ) -> str:
            return f"{id.type_name}:{id.node_id}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(f'{{ book(id: "{to_base64("LazyBook", "1")}") }}')
    assert not result.errors
    assert result.data == {"book": "LazyBook:1"}

    result = schema.execute_sync(f'{{ book(id: "{to_base64("Team", "1")}") }}')
    assert result.errors
    assert (
        result.errors[0].message
        == 'GlobalID type "Team" does not match expected type "LazyBook".'
    )


def test_global_id_non_type_metadata_is_ignored() -> None:
    """Plain strings, arbitrary objects and TypeVars are ordinary metadata."""

    @strawberry.type
    class Query:
        @strawberry.field
        def book(
            self,
            id: Annotated[GlobalID, "a note", 42, TypeVar("Ignored")],
        ) -> str:
            return f"{id.type_name}:{id.node_id}"

    schema = strawberry.Schema(query=Query)
    # no expected types were declared, so any GlobalID type name is accepted
    result = schema.execute_sync(f'{{ book(id: "{to_base64("Anything", "1")}") }}')
    assert not result.errors
    assert result.data == {"book": "Anything:1"}


def test_global_id_bare_lazy_reference_raises() -> None:
    with pytest.raises(TypeError, match="must include the type name"):

        @strawberry.type
        class Query:
            @strawberry.field
            def book(
                self,
                id: Annotated[
                    GlobalID,
                    strawberry.lazy("tests.relay.lazy_global_id_types"),
                ],
            ) -> str:
                return ""


def test_global_id_expected_type_nested_in_optional_list_raises() -> None:
    with pytest.raises(TypeError, match="only supported directly on an argument"):

        @strawberry.type
        class Query:
            @strawberry.field
            def books(self, ids: Optional[list[Annotated[GlobalID, Book]]]) -> str:
                return ""


def test_global_id_expected_type_nested_in_list_optional_raises() -> None:
    with pytest.raises(TypeError, match="only supported directly on an argument"):

        @strawberry.type
        class Query:
            @strawberry.field
            def books(self, ids: list[Optional[Annotated[GlobalID, Book]]]) -> str:
                return ""


def test_global_id_expected_type_nested_in_list_list_raises() -> None:
    with pytest.raises(TypeError, match="only supported directly on an argument"):

        @strawberry.type
        class Query:
            @strawberry.field
            def books(self, ids: list[list[Annotated[GlobalID, Book]]]) -> str:
                return ""


def test_global_id_expected_type_nested_in_outer_annotated_raises() -> None:
    with pytest.raises(TypeError, match="only supported directly on an argument"):

        @strawberry.type
        class Query:
            @strawberry.field
            def books(
                self, ids: Annotated[list[Annotated[GlobalID, Book]], "metadata"]
            ) -> str:
                return ""


def test_global_id_expected_type_nested_in_tuple_raises() -> None:
    with pytest.raises(TypeError, match="only supported directly on an argument"):

        @strawberry.type
        class Query:
            @strawberry.field
            def books(self, ids: tuple[Annotated[GlobalID, Book], ...]) -> str:
                return ""


def test_global_id_expected_type_union_of_two_annotated_raises() -> None:
    with pytest.raises(TypeError, match="only supported directly on an argument"):

        @strawberry.type
        class Query:
            @strawberry.field
            def book(
                self,
                id: Union[Annotated[GlobalID, Book], Annotated[GlobalID, Team]],
            ) -> str:
                return ""


def test_global_id_generic_expected_type_raises() -> None:
    with pytest.raises(TypeError, match="Generic aliases are not supported"):

        @strawberry.type
        class Query:
            @strawberry.field
            def book(self, id: Annotated[GlobalID, GenericBox[int]]) -> str:
                return ""


def test_global_id_lazy_resolution_error_is_clear() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def book(
            self,
            id: Annotated[
                GlobalID,
                Annotated[
                    "Ghost",  # noqa: F821, UP037
                    strawberry.lazy("tests.relay.nonexistent_lazy_module"),
                ],
            ],
        ) -> str:
            return ""

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(f'{{ book(id: "{to_base64("Ghost", "1")}") }}')
    assert result.errors
    assert "Could not resolve lazy GlobalID expected type" in result.errors[0].message


def test_global_id_expected_type_on_container_annotation_raises() -> None:
    with pytest.raises(TypeError, match="only supported when the annotated type"):

        @strawberry.type
        class Query:
            @strawberry.field
            def books(self, ids: Annotated[list[GlobalID], Book]) -> str:
                return ""

    with pytest.raises(TypeError, match="only supported when the annotated type"):

        @strawberry.type
        class OptionalQuery:
            @strawberry.field
            def books(self, ids: Annotated[Optional[list[GlobalID]], Book]) -> str:
                return ""

    with pytest.raises(TypeError, match="only supported when the annotated type"):

        @strawberry.type
        class MaybeQuery:
            @strawberry.field
            def books(self, ids: Annotated[strawberry.Maybe[GlobalID], Book]) -> str:
                return ""


def test_global_id_expected_type_nested_plain_class_raises() -> None:
    with pytest.raises(TypeError, match="only supported directly on an argument"):

        @strawberry.type
        class Query:
            @strawberry.field
            def books(self, ids: list[Annotated[GlobalID, PlainClass]]) -> str:
                return ""


def test_global_id_expected_type_on_input_field_raises() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def books(self, filter: GlobalIDInput) -> str:
            return ""

    with pytest.raises(TypeError, match="not supported on input object fields"):
        strawberry.Schema(query=Query)

    @strawberry.type
    class NestedQuery:
        @strawberry.field
        def books(self, filter: GlobalIDNestedInput) -> str:
            return ""

    with pytest.raises(TypeError, match="not supported on input object fields"):
        strawberry.Schema(query=NestedQuery)

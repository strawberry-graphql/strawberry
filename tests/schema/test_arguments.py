import textwrap
from enum import Enum
from textwrap import dedent
from typing import Annotated, Generic, Optional, TypeVar

import pytest

import strawberry
from strawberry import relay
from strawberry.directive import DirectiveLocation, DirectiveValue
from strawberry.types.unset import UNSET


def test_argument_descriptions():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(  # type: ignore
            name: Annotated[
                str, strawberry.argument(description="Your name")
            ] = "Patrick",
        ) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        '''\
        type Query {
          hello(
            """Your name"""
            name: String! = "Patrick"
          ): String!
        }'''
    )


def test_argument_deprecation_reason():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(  # type: ignore
            name: Annotated[
                str, strawberry.argument(deprecation_reason="Your reason")
            ] = "Patrick",
        ) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String! = "Patrick" @deprecated(reason: "Your reason")): String!
        }"""
    )


def test_argument_names():
    @strawberry.input
    class HelloInput:
        name: str = strawberry.field(default="Patrick", description="Your name")

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self, input_: Annotated[HelloInput, strawberry.argument(name="input")]
        ) -> str:
            return f"Hi {input_.name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        '''\
        input HelloInput {
          """Your name"""
          name: String! = "Patrick"
        }

        type Query {
          hello(input: HelloInput!): String!
        }'''
    )


def test_argument_with_default_value_none():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: str | None = None) -> str:
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String = null): String!
        }"""
    )


def test_optional_argument_unset():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: str | None = UNSET, age: int | None = UNSET) -> str:
            if name is UNSET:
                return "Hi there"
            return f"Hi {name}"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String, age: Int): String!
        }"""
    )

    result = schema.execute_sync(
        """
        query {
            hello
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "Hi there"}


def test_optional_input_field_unset():
    @strawberry.input
    class TestInput:
        name: str | None = UNSET
        age: int | None = UNSET

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, input: TestInput) -> str:
            if input.name is UNSET:
                return "Hi there"
            return f"Hi {input.name}"

    schema = strawberry.Schema(query=Query)

    assert (
        str(schema)
        == dedent(
            """
        type Query {
          hello(input: TestInput!): String!
        }

        input TestInput {
          name: String
          age: Int
        }
        """
        ).strip()
    )

    result = schema.execute_sync(
        """
        query {
            hello(input: {})
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "Hi there"}


def test_setting_metadata_on_argument():
    field_definition = None

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self,
            info: strawberry.Info,
            input: Annotated[str, strawberry.argument(metadata={"test": "foo"})],
        ) -> str:
            nonlocal field_definition
            field_definition = info._field
            return f"Hi {input}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            hello(input: "there")
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "Hi there"}

    assert field_definition
    assert field_definition.arguments[0].metadata == {
        "test": "foo",
    }


def test_argument_parse_order():
    """Check early early exit from argument parsing due to finding ``info``.

    Reserved argument parsing, which interally also resolves annotations, exits early
    after detecting the ``info`` argumnent. As a result, the annotation of the ``id_``
    argument in `tests.schema.test_annotated.type_a.Query` is never resolved. This
    results in `StrawberryArgument` not being able to detect that ``id_`` makes use of
    `typing.Annotated` and `strawberry.argument`.

    This behavior is fixed by by ensuring that `StrawberryArgument` makes use of the new
    `StrawberryAnnotation.evaluate` method instead of consuming the raw annotation.

    An added benefit of this fix is that by removing annotation resolving code from
    `StrawberryResolver` and making it a part of `StrawberryAnnotation`, it makes it
    possible for `StrawberryArgument` and `StrawberryResolver` to share the same type
    evaluation cache.

    Refer to: https://github.com/strawberry-graphql/strawberry/issues/2855
    """
    from tests.schema.test_annotated import type_a, type_b

    expected = """
    type Query {
      getTesting(id: UUID!): String
    }

    scalar UUID
    """

    schema_a = strawberry.Schema(type_a.Query)
    schema_b = strawberry.Schema(type_b.Query)

    assert str(schema_a) == str(schema_b)
    assert str(schema_a) == textwrap.dedent(expected).strip()


def test_input_instances_as_argument_defaults():
    @strawberry.input
    class Filter:
        limit: int = 10

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self, filter: Filter = Filter(limit=5)) -> int:
            return filter.limit

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ items }")

    assert not result.errors
    assert result.data == {"items": 5}

    result = schema.execute_sync("{ items(filter: { limit: 3 }) }")

    assert not result.errors
    assert result.data == {"items": 3}


def test_input_instances_as_input_field_defaults():
    @strawberry.input
    class Pagination:
        limit: int = 10

    @strawberry.input
    class Filter:
        pagination: Pagination = strawberry.field(
            default_factory=lambda: Pagination(limit=5)
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self, filter: Filter) -> int:
            return filter.pagination.limit

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ items(filter: {}) }")

    assert not result.errors
    assert result.data == {"items": 5}


def test_introspection_of_input_instances_as_defaults():
    @strawberry.input
    class Pagination:
        limit: int = 10

    @strawberry.input
    class Filter:
        pagination: Pagination = strawberry.field(
            default_factory=lambda: Pagination(limit=5)
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self, filter: Filter = Filter(pagination=Pagination(limit=3))) -> int:
            return filter.pagination.limit

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        {
            query: __type(name: "Query") { fields { args { defaultValue } } }
            filter: __type(name: "Filter") { inputFields { defaultValue } }
        }
        """
    )

    assert not result.errors
    assert result.data == {
        "query": {
            "fields": [{"args": [{"defaultValue": "{ pagination: { limit: 3 } }"}]}]
        },
        "filter": {"inputFields": [{"defaultValue": "{ limit: 5 }"}]},
    }


def test_printing_input_instances_as_defaults():
    @strawberry.enum
    class Order(Enum):
        ASC = "asc"
        DESC = "desc"

    @strawberry.input
    class Filter:
        order: Order = Order.ASC
        query: Optional[str] = None
        limit: Optional[int] = 10
        tags: list[str] = strawberry.field(default_factory=list)
        cursor: strawberry.Maybe[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def items(
            self,
            default: Filter = Filter(order=Order.DESC, cursor=None),
            unlimited: Filter = Filter(limit=None, cursor=strawberry.Some(None)),
            filters: list[Filter] = [Filter(tags=["a"], cursor=strawberry.Some("b"))],  # noqa: B006
        ) -> int:
            return 1

    schema = strawberry.Schema(query=Query)

    items = next(line for line in str(schema).splitlines() if "items(" in line)

    # `None` values are only printed when the field's default isn't `None`
    assert items == (
        "  items(default: Filter! = { order: DESC, limit: 10, tags: [] }, "
        "unlimited: Filter! = { order: ASC, limit: null, tags: [], cursor: null }, "
        'filters: [Filter!]! = [{ order: ASC, limit: 10, tags: ["a"], cursor: "b" }]): Int!'
    )


def test_each_request_gets_its_own_input_instance_default():
    @strawberry.input
    class Filter:
        limit: int = 10

    @strawberry.type
    class Query:
        @strawberry.field
        def limit(self, filter: Filter = Filter(limit=5)) -> int:
            limit = filter.limit
            filter.limit = 0

            return limit

    schema = strawberry.Schema(query=Query)

    for _ in range(2):
        result = schema.execute_sync("{ limit }")

        assert not result.errors
        assert result.data == {"limit": 5}


@pytest.mark.parametrize(
    ("query", "variables"),
    [
        ("{ search(filter: {}) }", None),
        ("query ($filter: Filter!) { search(filter: $filter) }", {"filter": {}}),
    ],
    ids=["inline", "variables"],
)
def test_each_request_gets_its_own_list_input_field_defaults(
    query: str, variables: dict[str, object] | None
):
    @strawberry.input
    class Filter:
        tags: list[str] = strawberry.field(default_factory=lambda: ["base"])
        groups: list[list[str]] = strawberry.field(default_factory=lambda: [["base"]])
        labels: list[str | None] | None = strawberry.field(
            default_factory=lambda: ["base"]
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: Filter) -> list[list[str | None]]:
            assert filter.labels is not None

            for value in (filter.tags, filter.groups[0], filter.labels):
                value.append("added")

            return [filter.tags, *filter.groups, filter.labels]

    schema = strawberry.Schema(query=Query)
    printed_schema = str(schema)

    for _ in range(2):
        result = schema.execute_sync(query, variable_values=variables)

        assert not result.errors
        assert result.data == {"search": [["base", "added"]] * 3}

    assert str(schema) == printed_schema


@pytest.mark.parametrize(
    "query",
    [
        "{ search }",
        """
        query ($tags: [String!], $groups: [[String!]!], $labels: [String],
               $filter: Filter) {
            search(tags: $tags, groups: $groups, labels: $labels, filter: $filter)
        }
        """,
    ],
    ids=["inline", "variables"],
)
def test_each_request_gets_its_own_list_argument_defaults(query: str):
    @strawberry.input
    class Filter:
        tags: list[str]
        labels: strawberry.Maybe[list[str]]

    @strawberry.type
    class Query:
        @strawberry.field
        def search(
            self,
            tags: list[str] = ["base"],  # noqa: B006
            groups: list[list[str]] = [["base"]],  # noqa: B006
            labels: list[str | None] | None = ["base"],  # noqa: B006
            filter: Filter = Filter(tags=["base"], labels=strawberry.Some(["base"])),
        ) -> list[list[str | None]]:
            assert labels is not None
            assert filter.labels is not None

            values = [tags, *groups, labels, filter.tags, filter.labels.value]

            for value in values:
                value.append("added")

            return values

    schema = strawberry.Schema(query=Query)
    printed_schema = str(schema)

    for _ in range(2):
        result = schema.execute_sync(query, variable_values={})

        assert not result.errors
        assert result.data == {"search": [["base", "added"]] * 5}

    assert str(schema) == printed_schema


def test_each_request_gets_its_own_list_directive_argument_defaults():
    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def tag(value: DirectiveValue[str], tags: list[str] = ["base"]) -> str:  # noqa: B006
        tags.append("added")

        return f"{value} {tags}"

    @strawberry.type
    class Query:
        name: str = "jam"

    schema = strawberry.Schema(query=Query, directives=[tag])
    printed_schema = str(schema)

    for _ in range(2):
        result = schema.execute_sync("{ name @tag }", root_value=Query())

        assert not result.errors
        assert result.data == {"name": "jam ['base', 'added']"}

    assert str(schema) == printed_schema


def test_generic_input_instances_as_defaults():
    T = TypeVar("T")

    @strawberry.input
    class Page(Generic[T]):
        after: Optional[T] = None
        limit: int = 10

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self, page: Page[int] = Page(after=3, limit=5)) -> str:
            return f"{page.after} {page.limit}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ items }")

    assert not result.errors
    assert result.data == {"items": "3 5"}


def test_dicts_as_input_type_defaults():
    @strawberry.input
    class Pagination:
        page_size: int = 10
        cursor: Optional[str] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def items(
            self,
            by_python_name: Pagination = {"page_size": 5, "cursor": None},  # type: ignore[assignment]  # noqa: B006
            by_graphql_name: Pagination = {"pageSize": 3},  # type: ignore[assignment]  # noqa: B006
        ) -> list[int]:
            return [by_python_name.page_size, by_graphql_name.page_size]

    schema = strawberry.Schema(query=Query)

    assert (
        "items(byPythonName: Pagination! = { pageSize: 5 }, "
        "byGraphqlName: Pagination! = { pageSize: 3 }): [Int!]!"
    ) in str(schema)

    result = schema.execute_sync(
        '{ items __type(name: "Query") { fields { args { defaultValue } } } }'
    )

    assert not result.errors
    assert result.data == {
        "items": [5, 3],
        "__type": {
            "fields": [
                {
                    "args": [
                        {"defaultValue": "{ pageSize: 5 }"},
                        {"defaultValue": "{ pageSize: 3 }"},
                    ]
                }
            ]
        },
    }


def test_dict_defaults_with_explicit_nulls_for_maybe_fields():
    @strawberry.input
    class Patch:
        name: strawberry.Maybe[Optional[str]]
        age: strawberry.Maybe[Optional[int]] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def patch(
            self,
            patch: Patch = {"name": None, "age": 3},  # type: ignore[assignment]  # noqa: B006
        ) -> str:
            return f"{patch.name!r} {patch.age!r}"

    schema = strawberry.Schema(query=Query)

    # unlike an attribute set to `None`, `None` in a dict is an explicit null
    assert "patch(patch: Patch! = { name: null, age: 3 }): String!" in str(schema)

    result = schema.execute_sync("{ patch }")

    assert not result.errors
    assert result.data == {"patch": "Some(None) Some(3)"}


def test_global_ids_in_defaults():
    @strawberry.input
    class Filter:
        user_id: relay.GlobalID

    @strawberry.type
    class Query:
        @strawberry.field
        def user_ids(
            self,
            id: relay.GlobalID = relay.GlobalID("User", "1"),
            filter: Filter = Filter(user_id=relay.GlobalID("User", "2")),
        ) -> list[str]:
            return [id.node_id, filter.user_id.node_id]

    schema = strawberry.Schema(query=Query)

    assert (
        'userIds(id: ID! = "VXNlcjox", filter: Filter! = { userId: "VXNlcjoy" })'
        in str(schema)
    )

    result = schema.execute_sync("{ userIds }")

    assert not result.errors
    assert result.data == {"userIds": ["1", "2"]}

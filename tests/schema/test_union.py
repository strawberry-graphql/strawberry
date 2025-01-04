import sys
import textwrap
from dataclasses import dataclass
from textwrap import dedent
from typing import Annotated, Generic, Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.exceptions import InvalidUnionTypeError
from strawberry.types.lazy_type import lazy


def test_union_as_field():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Query:
        ab: Union[A, B] = strawberry.field(default_factory=lambda: A(a=5))

    schema = strawberry.Schema(query=Query)
    query = """{
        ab {
            __typename,

            ... on A {
                a
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["ab"] == {"__typename": "A", "a": 5}


def test_union_as_field_inverse():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Query:
        ab: Union[A, B] = strawberry.field(default_factory=lambda: B(b=5))

    schema = strawberry.Schema(query=Query)
    query = """{
        ab {
            __typename,

            ... on B {
                b
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["ab"] == {"__typename": "B", "b": 5}


def test_cannot_use_non_strawberry_fields_for_the_union():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Query:
        ab: Union[A, B] = "ciao"

    schema = strawberry.Schema(query=Query)
    query = """{
        ab {
            __typename,

            ... on A {
                a
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert (
        result.errors[0].message
        == 'The type "<class \'str\'>" cannot be resolved for the field "ab" '
        ", are you using a strawberry.field?"
    )


def test_union_as_mutation_return():
    @strawberry.type
    class A:
        x: int

    @strawberry.type
    class B:
        y: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def hello(self) -> Union[A, B]:
            return B(y=5)

    schema = strawberry.Schema(query=A, mutation=Mutation)

    query = """
    mutation {
        hello {
            __typename

            ... on A {
                x
            }

            ... on B {
                y
            }
        }
    }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["hello"] == {"__typename": "B", "y": 5}


def test_types_not_included_in_the_union_are_rejected():
    @strawberry.type
    class Outside:
        c: int

    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def hello(self) -> Union[A, B]:
            return Outside(c=5)  # type:ignore

    schema = strawberry.Schema(query=A, mutation=Mutation, types=[Outside])

    query = """
    mutation {
        hello {
            __typename

            ... on A {
                a
            }

            ... on B {
                b
            }
        }
    }
    """

    result = schema.execute_sync(query)

    assert (
        result.errors[0].message == "The type "
        "\"<class 'tests.schema.test_union.test_types_not_included_in_the_union_are_rejected.<locals>.Outside'>\""
        ' of the field "hello" '
        "is not in the list of the types of the union: \"['A', 'B']\""
    )


def test_unknown_types_are_rejected():
    @strawberry.type
    class Outside:
        c: int

    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> Union[A, B]:
            return Outside(c=5)  # type:ignore

    schema = strawberry.Schema(query=Query)

    query = """
    {
        hello {
            ... on A {
                a
            }
        }
    }
    """

    result = schema.execute_sync(query)

    assert "Outside" in result.errors[0].message


def test_named_union():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = Annotated[Union[A, B], strawberry.union(name="Result")]

    @strawberry.type
    class Query:
        ab: Result = strawberry.field(default_factory=lambda: A(a=5))

    schema = strawberry.Schema(query=Query)

    query = """{
        __type(name: "Result") {
            kind
            description
        }

        ab {
            __typename,

            ... on A {
                a
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["ab"] == {"__typename": "A", "a": 5}
    assert result.data["__type"] == {"kind": "UNION", "description": None}


def test_named_union_description():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = Annotated[
        Union[A, B], strawberry.union(name="Result", description="Example Result")
    ]

    @strawberry.type
    class Query:
        ab: Result = strawberry.field(default_factory=lambda: A(a=5))

    schema = strawberry.Schema(query=Query)

    query = """{
        __type(name: "Result") {
            kind
            description
        }

        ab {
            __typename,

            ... on A {
                a
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["ab"] == {"__typename": "A", "a": 5}
    assert result.data["__type"] == {"kind": "UNION", "description": "Example Result"}


def test_can_use_union_in_optional():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = Annotated[Union[A, B], strawberry.union(name="Result")]

    @strawberry.type
    class Query:
        ab: Optional[Result] = None

    schema = strawberry.Schema(query=Query)

    query = """{
        __type(name: "Result") {
            kind
            description
        }

        ab {
            __typename,

            ... on A {
                a
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["ab"] is None


def test_multiple_unions():
    @strawberry.type
    class CoolType:
        @strawberry.type
        class UnionA1:
            value: int

        @strawberry.type
        class UnionA2:
            value: int

        @strawberry.type
        class UnionB1:
            value: int

        @strawberry.type
        class UnionB2:
            value: int

        field1: Union[UnionA1, UnionA2]
        field2: Union[UnionB1, UnionB2]

    schema = strawberry.Schema(query=CoolType)

    query = """
        {
            __type(name:"CoolType") {
                name
                description
                fields {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["__type"] == {
        "description": None,
        "fields": [{"name": "field1"}, {"name": "field2"}],
        "name": "CoolType",
    }


def test_union_used_multiple_times():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    MyUnion = Annotated[Union[A, B], strawberry.union("MyUnion")]

    @strawberry.type
    class Query:
        field1: MyUnion
        field2: MyUnion

    schema = strawberry.Schema(query=Query)

    assert schema.as_str() == dedent(
        """\
        type A {
          a: Int!
        }

        type B {
          b: Int!
        }

        union MyUnion = A | B

        type Query {
          field1: MyUnion!
          field2: MyUnion!
        }"""
    )


def test_union_explicit_type_resolution():
    @dataclass
    class ADataclass:
        a: int

    @strawberry.type
    class A:
        a: int

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return isinstance(obj, ADataclass)

    @strawberry.type
    class B:
        b: int

    MyUnion = Annotated[Union[A, B], strawberry.union("MyUnion")]

    @strawberry.type
    class Query:
        @strawberry.field
        def my_field(self) -> MyUnion:
            return ADataclass(a=1)  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = "{ myField { __typename, ... on A { a }, ... on B { b } } }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"myField": {"__typename": "A", "a": 1}}


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="pipe syntax for union is only available on python 3.10+",
)
def test_union_optional_with_or_operator():
    """Verify that the `|` operator is supported when annotating unions as
    optional in schemas.
    """

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Dog:
        name: str

    animal_union = Annotated[Cat | Dog, strawberry.union("Animal")]

    @strawberry.type
    class Query:
        @strawberry.field
        def animal(self) -> animal_union | None:
            return None

    schema = strawberry.Schema(query=Query)
    query = """{
        animal {
            __typename
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["animal"] is None


def test_union_with_input_types():
    """Verify that union of input types raises an error."""

    @strawberry.type
    class User:
        name: str
        age: int

    @strawberry.input
    class A:
        a: str

    @strawberry.input
    class B:
        b: str

    @strawberry.input
    class Input:
        name: str
        something: Union[A, B]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, data: Input) -> User:
            return User(name=data.name, age=100)

    with pytest.raises(
        TypeError, match="Union for A is not supported because it is an Input type"
    ):
        strawberry.Schema(query=Query)


def test_union_with_similar_nested_generic_types():
    """Previously this failed due to an edge case where Strawberry would choose AContainer
    as the resolved type for container_b due to the inability to exactly match the
    nested generic `Container.items`.
    """
    T = TypeVar("T")

    @strawberry.type
    class Container(Generic[T]):
        items: list[T]

    @strawberry.type
    class A:
        a: str

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Query:
        @strawberry.field
        def container_a(self) -> Union[Container[A], A]:
            return Container(items=[A(a="hello")])

        @strawberry.field
        def container_b(self) -> Union[Container[B], B]:
            return Container(items=[B(b=3)])

    schema = strawberry.Schema(query=Query)

    query = """
     {
        containerA {
            __typename
            ... on AContainer {
                items {
                    a
                }
            }
            ... on A {
                a
            }
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.data["containerA"]["items"][0]["a"] == "hello"

    query = """
     {
        containerB {
            __typename
            ... on BContainer {
                items {
                    b
                }
            }
            ... on B {
                b
            }
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.data["containerB"]["items"][0]["b"] == 3


def test_lazy_union():
    """Previously this failed to evaluate generic parameters on lazy types"""
    TypeA = Annotated["TypeA", lazy("tests.schema.test_lazy_types.type_a")]
    TypeB = Annotated["TypeB", lazy("tests.schema.test_lazy_types.type_b")]

    @strawberry.type
    class Query:
        @strawberry.field
        def a(self) -> Union[TypeA, TypeB]:
            from tests.schema.test_lazy_types.type_a import TypeA

            return TypeA(list_of_b=[])

        @strawberry.field
        def b(self) -> Union[TypeA, TypeB]:
            from tests.schema.test_lazy_types.type_b import TypeB

            return TypeB()

    schema = strawberry.Schema(query=Query)

    query = """
     {
        a {
            __typename
        }
        b {
            __typename
        }
    }
    """

    result = schema.execute_sync(query)

    assert result.data["a"]["__typename"] == "TypeA"
    assert result.data["b"]["__typename"] == "TypeB"


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError, match="Type `int` cannot be used in a GraphQL Union"
)
def test_error_with_invalid_annotated_type():
    @strawberry.type
    class Something:
        h: str

    AnnotatedInt = Annotated[int, "something_else"]

    @strawberry.type
    class Query:
        union: Union[Something, AnnotatedInt]

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError, match="Type `int` cannot be used in a GraphQL Union"
)
def test_raises_on_union_with_int():
    global ICanBeInUnion

    @strawberry.type
    class ICanBeInUnion:
        foo: str

    @strawberry.type
    class Query:
        union: Union[ICanBeInUnion, int]

    strawberry.Schema(query=Query)

    del ICanBeInUnion


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError,
    match=r"Type `list\[...\]` cannot be used in a GraphQL Union",
)
def test_raises_on_union_with_list_str():
    global ICanBeInUnion

    @strawberry.type
    class ICanBeInUnion:
        foo: str

    @strawberry.type
    class Query:
        union: Union[ICanBeInUnion, list[str]]

    strawberry.Schema(query=Query)

    del ICanBeInUnion


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError,
    match=r"Type `list\[...\]` cannot be used in a GraphQL Union",
)
def test_raises_on_union_with_list_str_38():
    global ICanBeInUnion

    @strawberry.type
    class ICanBeInUnion:
        foo: str

    @strawberry.type
    class Query:
        union: Union[ICanBeInUnion, list[str]]

    strawberry.Schema(query=Query)

    del ICanBeInUnion


@pytest.mark.raises_strawberry_exception(
    InvalidUnionTypeError, match="Type `Always42` cannot be used in a GraphQL Union"
)
def test_raises_on_union_of_custom_scalar():
    @strawberry.type
    class ICanBeInUnion:
        foo: str

    @strawberry.scalar(serialize=lambda x: 42, parse_value=lambda x: Always42())
    class Always42:
        pass

    @strawberry.type
    class Query:
        union: Annotated[
            Union[Always42, ICanBeInUnion], strawberry.union(name="ExampleUnion")
        ]

    strawberry.Schema(query=Query)


def test_union_of_unions():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        name: str

    @strawberry.type
    class SpecificError:
        name: str

    @strawberry.type
    class EvenMoreSpecificError:
        name: str

    ErrorUnion = Union[SpecificError, EvenMoreSpecificError]

    @strawberry.type
    class Query:
        user: Union[User, Error]
        error: Union[User, ErrorUnion]

    schema = strawberry.Schema(query=Query)

    expected_schema = textwrap.dedent(
        """
        type Error {
          name: String!
        }

        type EvenMoreSpecificError {
          name: String!
        }

        type Query {
          user: UserError!
          error: UserSpecificErrorEvenMoreSpecificError!
        }

        type SpecificError {
          name: String!
        }

        type User {
          name: String!
        }

        union UserError = User | Error

        union UserSpecificErrorEvenMoreSpecificError = User | SpecificError | EvenMoreSpecificError
        """
    ).strip()

    assert str(schema) == expected_schema


def test_single_union():
    @strawberry.type
    class A:
        a: int = 5

    @strawberry.type
    class Query:
        something: Annotated[A, strawberry.union(name="Something")] = strawberry.field(
            default_factory=A
        )

    schema = strawberry.Schema(query=Query)
    query = """{
        something {
            __typename,

            ... on A {
                a
            }
        }
    }"""

    assert (
        str(schema)
        == textwrap.dedent(
            """
        type A {
          a: Int!
        }

        type Query {
          something: Something!
        }

        union Something = A
        """
        ).strip()
    )

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["something"] == {"__typename": "A", "a": 5}

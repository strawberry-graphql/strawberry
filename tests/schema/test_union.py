import sys
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional, Union

import pytest

import strawberry


def test_union_as_field():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    @strawberry.type
    class Query:
        ab: Union[A, B] = A(a=5)

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
        ab: Union[A, B] = B(b=5)

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


def test_cannot_use_non_strawberry_fields_in_the_union():
    @strawberry.type
    class UnionTypeOne:
        one: str

    class UnionTypeTwo:
        two: str

    United = Union[
        UnionTypeOne,
        UnionTypeTwo,
    ]

    @strawberry.type
    class Transaction:
        title: str
        details: Optional[United] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self) -> Transaction:
            return Transaction(title="title")

    with pytest.raises(
        TypeError, match="Type `UnionTypeTwo` cannot be used in a GraphQL Union"
    ):
        strawberry.Schema(query=Query)


def test_cannot_use_scalars_in_the_union():
    @strawberry.type
    class UnionTypeOne:
        one: str

    United = Union[
        UnionTypeOne,
        int,
    ]

    @strawberry.type
    class Transaction:
        title: str
        details: Optional[United] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self) -> Transaction:
            return Transaction(title="title")

    with pytest.raises(TypeError, match="Type `int` cannot be used in a GraphQL Union"):
        strawberry.Schema(query=Query)


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
        "\"<class 'tests.schema.test_union.test_types_not_included_in_the_union_are_rejected.<locals>.Outside'>\""  # noqa
        ' of the field "hello" '
        "is not in the list of the types of the union: \"['A', 'B']\""
    )


def test_named_union():
    @strawberry.type
    class A:
        a: int

    @strawberry.type
    class B:
        b: int

    Result = strawberry.union("Result", (A, B))

    @strawberry.type
    class Query:
        ab: Result = A(a=5)

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

    Result = strawberry.union("Result", (A, B), description="Example Result")

    @strawberry.type
    class Query:
        ab: Result = A(a=5)

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

    Result = strawberry.union("Result", (A, B))

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

    MyUnion = strawberry.union("MyUnion", types=(A, B))

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

    MyUnion = strawberry.union("MyUnion", types=(A, B))

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
    """
    Verify that the `|` operator is supported when annotating unions as
    optional in schemas.
    """

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Dog:
        name: str

    animal_union = strawberry.union("Animal", (Cat, Dog))

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

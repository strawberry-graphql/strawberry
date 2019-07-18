from typing import Union

import strawberry
from graphql import graphql_sync


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

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["ab"] == {"__typename": "A", "a": 5}


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

    result = graphql_sync(schema, query)

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
        def hello(self, info) -> Union[A, B]:
            # TODO: mypy is unable to understand that B is a dataclass
            return B(y=5)  # type:ignore

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

    result = graphql_sync(schema, query)

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
        def hello(self, info) -> Union[A, B]:
            # TODO: mypy is unable to understand that Outside is a dataclass
            return Outside(c=5)  # type:ignore

    schema = strawberry.Schema(query=A, mutation=Mutation)

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

    result = graphql_sync(schema, query)

    assert (
        result.errors[0].message == "The type "
        "\"<class 'tests.test_union.test_types_not_included_in_the_union_are_rejected.<locals>.Outside'>\""  # noqa
        ' of the field "hello" '
        "is not in the list of the types of the union: \"['A', 'B']\""
    )

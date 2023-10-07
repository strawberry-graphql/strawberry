from __future__ import annotations

import textwrap
from uuid import UUID

import strawberry
from strawberry.field_extensions import InputMutationExtension


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self) -> str:
        return "hi"


@strawberry.type
class Mutation:
    @strawberry.mutation(extensions=[InputMutationExtension()])
    async def buggy(self, some_id: UUID) -> None:
        del some_id


def test_schema():
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    expected_schema = '''
    input BuggyInput {
      someId: UUID!
    }

    type Mutation {
      buggy(
        """Input data for `buggy` mutation"""
        input: BuggyInput!
      ): Void
    }

    type Query {
      hello: String!
    }

    scalar UUID

    """Represents NULL values"""
    scalar Void
    '''

    assert textwrap.dedent(expected_schema).strip() == str(schema).strip()

import textwrap
from typing import Annotated

import strawberry
from strawberry.field_extensions import InputMutationExtension


@strawberry.federation.type
class Fruit:
    name: str
    color: str


@strawberry.federation.type
class Query:
    @strawberry.field
    def hello(self) -> str:  # pragma: no cover
        return "hi"


@strawberry.federation.type
class Mutation:
    @strawberry.federation.mutation(extensions=[InputMutationExtension()])
    def create_fruit(
        self,
        name: str,
        color: Annotated[
            str,
            strawberry.federation.argument(
                description="The color of the fruit",
            ),
        ],
    ) -> Fruit:
        return Fruit(
            name=name,
            color=color,
        )


schema = strawberry.federation.Schema(query=Query, mutation=Mutation)


def test_schema():
    expected = '''
    input CreateFruitInput {
      name: String!

      """The color of the fruit"""
      color: String!
    }

    type Fruit {
      name: String!
      color: String!
    }

    type Mutation {
      createFruit(
        """Input data for `createFruit` mutation"""
        input: CreateFruitInput!
      ): Fruit!
    }

    type Query {
      _service: _Service!
      hello: String!
    }

    scalar _Any

    type _Service {
      sdl: String!
    }
    '''
    assert str(schema).strip() == textwrap.dedent(expected).strip()


def test_input_mutation():
    result = schema.execute_sync(
        """
        mutation TestQuery ($input: CreateFruitInput!) {
            createFruit (input: $input) {
                ... on Fruit {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "input": {
                "name": "Dragonfruit",
                "color": "red",
            }
        },
    )
    assert result.errors is None
    assert result.data == {
        "createFruit": {
            "name": "Dragonfruit",
            "color": "red",
        },
    }

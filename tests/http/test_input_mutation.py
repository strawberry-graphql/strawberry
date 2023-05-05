import textwrap
from typing_extensions import Annotated

import strawberry
from strawberry.schema_directive import Location, schema_directive
from strawberry.types import Info


@schema_directive(
    locations=[Location.FIELD_DEFINITION],
    name="some_directive",
)
class SomeDirective:
    some: str
    directive: str


@strawberry.type
class Fruit:
    name: str
    color: str


@strawberry.type
class Query:
    @strawberry.input_mutation
    def create_fruit(
        self,
        info: Info,
        name: str,
        color: Annotated[
            str,
            strawberry.argument(
                description="The color of the fruit",
                directives=[SomeDirective(some="foo", directive="bar")],
            ),
        ],
    ) -> Fruit:
        return Fruit(
            name=name,
            color=color,
        )

    @strawberry.input_mutation
    async def create_fruit_async(
        self,
        info: Info,
        name: str,
        color: Annotated[str, object()],
    ) -> Fruit:
        return Fruit(
            name=name,
            color=color,
        )


schema = strawberry.Schema(query=Query)


def test_schema():
    expected = '''
    directive @some_directive(some: String!, directive: String!) on FIELD_DEFINITION

    input CreateFruitAsyncInput {
      name: String!
      color: String!
    }

    input CreateFruitInput {
      name: String!

      """The color of the fruit"""
      color: String! @some_directive(some: "foo", directive: "bar")
    }

    type Fruit {
      name: String!
      color: String!
    }

    type Query {
      createFruit(
        """Input data for `createFruit` mutation"""
        input: CreateFruitInput!
      ): Fruit!
      createFruitAsync(
        """Input data for `createFruitAsync` mutation"""
        input: CreateFruitAsyncInput!
      ): Fruit!
    }
    '''
    assert str(schema).strip() == textwrap.dedent(expected).strip()


def test_input_mutation():
    result = schema.execute_sync(
        """
        query TestQuery ($input: CreateFruitInput!) {
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


async def test_input_mutation_async():
    result = await schema.execute(
        """
        query TestQuery ($input: CreateFruitAsyncInput!) {
            createFruitAsync (input: $input) {
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
        "createFruitAsync": {
            "name": "Dragonfruit",
            "color": "red",
        },
    }

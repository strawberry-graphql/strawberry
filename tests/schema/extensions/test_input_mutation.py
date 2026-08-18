import textwrap
from typing import Annotated

import strawberry
from strawberry.field_extensions import InputMutationExtension
from strawberry.permission import BasePermission
from strawberry.schema_directive import Location, schema_directive


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
    @strawberry.field
    def hello(self) -> str:
        return "hi"


@strawberry.type
class Mutation:
    @strawberry.mutation(extensions=[InputMutationExtension()])
    def create_fruit(
        self,
        name: str,
        color: Annotated[
            str,
            strawberry.argument(
                description="The color of the fruit",
                directives=[SomeDirective(some="foo", directive="bar")],
            ),
        ],
        variety: Annotated[
            str | None,
            strawberry.argument(
                deprecation_reason="Use `color` instead",
            ),
        ] = None,
    ) -> Fruit:
        return Fruit(
            name=name,
            color=color,
        )

    @strawberry.mutation(extensions=[InputMutationExtension()])
    async def create_fruit_async(
        self,
        name: str,
        color: Annotated[str, object()],
    ) -> Fruit:
        return Fruit(
            name=name,
            color=color,
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)


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
      variety: String = null @deprecated(reason: "Use `color` instead")
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
      createFruitAsync(
        """Input data for `createFruitAsync` mutation"""
        input: CreateFruitAsyncInput!
      ): Fruit!
    }

    type Query {
      hello: String!
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


async def test_input_mutation_async():
    result = await schema.execute(
        """
        mutation TestQuery ($input: CreateFruitAsyncInput!) {
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


def test_input_is_unpacked_before_field_extensions_and_permissions_run():
    # The synthetic ``input`` argument is unpacked into the resolver's original
    # keyword arguments during argument conversion, so permission classes and
    # other field extensions see the individual arguments (``name``, ``color``)
    # rather than the wrapping ``input`` object.
    seen_kwargs = {}

    class RecordKwargs(BasePermission):
        message = "denied"

        def has_permission(self, source, info, **kwargs) -> bool:  # noqa: ANN003
            seen_kwargs.update(kwargs)
            return True

    @strawberry.type
    class Mutation:
        @strawberry.mutation(
            extensions=[InputMutationExtension()],
            permission_classes=[RecordKwargs],
        )
        def create_fruit(self, name: str, color: str) -> Fruit:
            return Fruit(name=name, color=color)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            createFruit(input: { name: "Banana", color: "yellow" }) {
                name
                color
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"createFruit": {"name": "Banana", "color": "yellow"}}
    assert seen_kwargs == {"name": "Banana", "color": "yellow"}

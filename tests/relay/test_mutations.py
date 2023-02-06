from strawberry.relay.utils import to_base64

from .schema import schema


def test_input_mutation():
    result = schema.execute_sync(
        """
        query TestQuery ($input: CreateFruitInput!) {
            createFruit (input: $input) {
                ... on Fruit {
                    id
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
            "id": to_base64("Fruit", 6),
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
                    id
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
            "id": to_base64("Fruit", 6),
            "name": "Dragonfruit",
            "color": "red",
        },
    }

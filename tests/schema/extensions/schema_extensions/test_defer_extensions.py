import pytest
from inline_snapshot import snapshot

import strawberry
from tests.conftest import skip_if_gql_32
from tests.schema.extensions.schema_extensions.conftest import (
    ExampleExtension,
)

pytestmark = skip_if_gql_32("GraphQL 3.3.0 is required for incremental execution")


@pytest.mark.xfail(reason="Not fully supported just yet")
async def test_basic_extension_with_defer(
    async_extension: type[ExampleExtension],
):
    @strawberry.type
    class Hero:
        id: strawberry.ID

        @strawberry.field
        async def name(self) -> str:
            return "Luke Skywalker"

    @strawberry.type
    class Query:
        @strawberry.field
        def hero(self) -> Hero:
            return Hero(id=strawberry.ID("1"))

    extension = async_extension()

    schema = strawberry.Schema(
        query=Query,
        extensions=[extension],
        config={"enable_experimental_incremental_execution": True},
    )

    result = await schema.execute(
        query="""
        query HeroNameQuery {
            hero {
                id
                ...NameFragment @defer
            }
        }
        fragment NameFragment on Hero {
            name
        }
        """,
    )

    initial = result.initial_result.formatted

    assert initial == snapshot(
        {
            "data": {"hero": {"id": "1"}},
            "hasNext": True,
            "pending": [{"path": ["hero"], "id": "0"}],
        }
    )

    async for subsequent in result.subsequent_results:
        assert subsequent.formatted == snapshot(
            {
                "completed": [
                    {
                        "id": "0",
                        "errors": [
                            {
                                "message": "String cannot represent value: <coroutine _async_resolver>",
                                "locations": [{"line": 9, "column": 13}],
                                "path": ["hero", "name"],
                            }
                        ],
                    }
                ],
                "hasNext": False,
            }
        )

    extension.assert_expected()

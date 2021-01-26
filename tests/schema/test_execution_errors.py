import pytest

import strawberry
from strawberry.extensions import Extension


class MyExtension(Extension):
    def get_results(self):
        return {"example": "example"}


def test_runs_parsing():
    @strawberry.type
    class Query:
        name: str

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
    """

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert result.errors[0].message == "Syntax Error: Expected Name, found <EOF>."


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:.* was never awaited:RuntimeWarning")
async def test_errors_when_running_async_in_sync_mode():
    @strawberry.type
    class Query:
        @strawberry.field
        async def name(self) -> str:
            return "Patrick"

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            name
        }
    """

    with pytest.raises(RuntimeError) as e:
        schema.execute_sync(query)

    assert e.value.args[0] == "GraphQL execution failed to complete synchronously."


@pytest.mark.asyncio
async def test_runs_parsing_async():
    @strawberry.type
    class Query:
        example: str

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
    """

    result = await schema.execute(query)

    assert len(result.errors) == 1
    assert result.errors[0].message == "Syntax Error: Expected Name, found <EOF>."

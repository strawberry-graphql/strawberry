import pytest

import strawberry
from strawberry.schema.config import StrawberryConfig


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

    result = schema.execute_sync(query)
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, RuntimeError)
    assert (
        result.errors[0].message
        == "GraphQL execution failed to complete synchronously."
    )


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


def test_suggests_fields_by_default():
    @strawberry.type
    class Query:
        name: str

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            ample
        }
    """

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "Cannot query field 'ample' on type 'Query'. Did you mean 'name'?"
    )


def test_can_disable_field_suggestions():
    @strawberry.type
    class Query:
        name: str

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(disable_field_suggestions=True)
    )

    query = """
        query {
            ample
        }
    """

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert result.errors[0].message == "Cannot query field 'ample' on type 'Query'."


def test_can_disable_field_suggestions_multiple_fields():
    @strawberry.type
    class Query:
        name: str
        age: str

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(disable_field_suggestions=True)
    )

    query = """
        query {
            ample
            ag
        }
    """

    result = schema.execute_sync(query)

    assert len(result.errors) == 2
    assert result.errors[0].message == "Cannot query field 'ample' on type 'Query'."
    assert result.errors[1].message == "Cannot query field 'ag' on type 'Query'."

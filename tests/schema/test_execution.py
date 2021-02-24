import textwrap
from typing import Optional

import pytest

import strawberry


@pytest.mark.parametrize("validate_queries", (True, False))
def test_enabling_query_validation_sync(validate_queries, mocker):
    extension_mock = mocker.Mock()
    extension_mock.get_results.return_value = {}

    extension_class_mock = mocker.Mock(return_value=extension_mock)

    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(query=Query, extensions=[extension_class_mock])

    query = """
        query {
            example
        }
    """

    result = schema.execute_sync(
        query, root_value=Query(), validate_queries=validate_queries
    )

    assert not result.errors

    assert extension_mock.on_validation_start.called is validate_queries
    assert extension_mock.on_validation_end.called is validate_queries


@pytest.mark.asyncio
@pytest.mark.parametrize("validate_queries", (True, False))
async def test_enabling_query_validation(validate_queries, mocker):
    extension_mock = mocker.Mock()
    extension_mock.get_results.return_value = {}

    extension_class_mock = mocker.Mock(return_value=extension_mock)

    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(query=Query, extensions=[extension_class_mock])

    query = """
        query {
            example
        }
    """

    result = await schema.execute(
        query, root_value=Query(), validate_queries=validate_queries
    )

    assert not result.errors

    assert extension_mock.on_validation_start.called is validate_queries
    assert extension_mock.on_validation_end.called is validate_queries


@pytest.mark.asyncio
async def test_invalid_query_with_validation_disabled():
    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
    """

    result = await schema.execute(query, root_value=Query())

    assert str(result.errors[0]) == (
        "Syntax Error: Expected Name, found <EOF>.\n\n"
        "GraphQL request:4:5\n"
        "3 |             example\n"
        "4 |     \n"
        "  |     ^"
    )


@pytest.mark.asyncio
async def test_asking_for_wrong_field():
    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            sample
        }
    """

    result = await schema.execute(query, root_value=Query(), validate_queries=False)

    assert result.errors is None
    assert result.data == {}


@pytest.mark.asyncio
async def test_sending_wrong_variables():
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self, value: str) -> int:
            return 1

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example(value: 123)
        }
    """

    result = await schema.execute(query, root_value=Query(), validate_queries=False)

    assert (
        str(result.errors[0])
        == textwrap.dedent(
            """
            Argument 'value' has invalid value 123.

            GraphQL request:3:28
            2 |         query {
            3 |             example(value: 123)
              |                            ^
            4 |         }
            """
        ).strip()
    )

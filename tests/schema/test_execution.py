from typing import Optional

import pytest

import strawberry


@pytest.mark.asyncio
@pytest.mark.parametrize("validate_queries", (True, False))
async def test_enabling_query_validation(validate_queries, mocker):
    extension_mock = mocker.Mock()
    extension_mock.get_results.return_value = {}

    extension_class_mock = mocker.Mock(return_value=extension_mock)

    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(
        query=Query,
        validate_queries=validate_queries,
        extensions=[extension_class_mock],
    )

    query = """
        query {
            example
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
    )

    assert not result.errors

    assert extension_mock.on_validation_start.called is validate_queries
    assert extension_mock.on_validation_end.called is validate_queries


@pytest.mark.asyncio
async def test_invalid_query_with_validation_disabled():
    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(
        query=Query,
        validate_queries=False,
    )

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

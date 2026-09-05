"""Test that assert_no_errors includes response.errors in the AssertionError message."""

from contextlib import nullcontext

import pytest

from strawberry.utils.await_maybe import await_maybe

QUERY_TO_NON_EXISTENT_FIELD = "{ nonExistentField { id } }"

NON_EXISTENT_FIELD_ERRORS = [
    {
        "message": "Cannot query field 'nonExistentField' on type 'Query'.",
        "locations": [{"line": 1, "column": 3}],
    }
]


@pytest.mark.parametrize(
    ("assert_no_errors", "expectation"),
    [(True, pytest.raises(AssertionError)), (False, nullcontext())],
)
async def test_query_with_assert_no_errors_option(
    graphql_client, assert_no_errors, expectation
):
    query = "{ ThisIsNotAValidQuery }"

    with expectation:
        await await_maybe(
            graphql_client.query(query, assert_no_errors=assert_no_errors)
        )


async def test_assert_no_errors_includes_response_errors_in_message(graphql_client):
    with pytest.raises(AssertionError) as exc_info:
        await await_maybe(graphql_client.query(QUERY_TO_NON_EXISTENT_FIELD))

    assert exc_info.value.args[0] == NON_EXISTENT_FIELD_ERRORS

from contextlib import nullcontext

import pytest

from strawberry.utils.await_maybe import await_maybe


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

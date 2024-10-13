from contextlib import nullcontext

import pytest

from strawberry.utils.await_maybe import await_maybe


@pytest.mark.parametrize("asserts_errors", [True, False])
async def test_query_asserts_errors_option_is_deprecated(
    graphql_client, asserts_errors
):
    with pytest.warns(
        DeprecationWarning,
        match="The `asserts_errors` argument has been renamed to `assert_no_errors`",
    ):
        await await_maybe(
            graphql_client.query("{ hello }", asserts_errors=asserts_errors)
        )


@pytest.mark.parametrize("option_name", ["asserts_errors", "assert_no_errors"])
@pytest.mark.parametrize(
    ("assert_no_errors", "expectation"),
    [(True, pytest.raises(AssertionError)), (False, nullcontext())],
)
async def test_query_with_assert_no_errors_option(
    graphql_client, option_name, assert_no_errors, expectation
):
    query = "{ ThisIsNotAValidQuery }"

    with expectation:
        await await_maybe(
            graphql_client.query(query, **{option_name: assert_no_errors})
        )

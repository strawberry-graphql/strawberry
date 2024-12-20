from contextlib import nullcontext

import pytest

from strawberry.utils.await_maybe import await_maybe


@pytest.mark.parametrize("asserts_errors", [True, False])
async def test_query_asserts_errors_option_is_deprecated(
    graphql_client, asserts_errors
):
    with pytest.deprecated_call(
        match="The `asserts_errors` argument has been renamed to `assert_no_errors`"
    ):
        await await_maybe(
            graphql_client.query("{ hello }", asserts_errors=asserts_errors)
        )


@pytest.mark.parametrize(
    ("option_name", "expectation1"),
    [("asserts_errors", pytest.deprecated_call()), ("assert_no_errors", nullcontext())],
)
@pytest.mark.parametrize(
    ("assert_no_errors", "expectation2"),
    [(True, pytest.raises(AssertionError)), (False, nullcontext())],
)
async def test_query_with_assert_no_errors_option(
    graphql_client, option_name, assert_no_errors, expectation1, expectation2
):
    query = "{ ThisIsNotAValidQuery }"

    with expectation1, expectation2:
        await await_maybe(
            graphql_client.query(query, **{option_name: assert_no_errors})
        )

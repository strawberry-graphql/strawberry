def test_assertion_error_not_raised_when_asserts_errors_is_false(graphql_client):
    query = "{  }"

    try:
        graphql_client.query(query, asserts_errors=False)
    except AssertionError:
        assert False

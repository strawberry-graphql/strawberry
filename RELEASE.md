Release type: minor

This release adds an implementation of the `GraphQLTestClient` for the `aiohttp` integration (in addition to the existing `asgi` and `Django` support). It hides the HTTP request's details and verifies that there are no errors in the response (this behavior can be disabled by passing `asserts_errors=False`). This makes it easier to test queries and makes your tests cleaner.

If you are using `pytest` you can add a fixture in `conftest.py`

```python
import pytest

from strawberry.aiohttp.test.client import GraphQLTestClient

@pytest.fixture
def graphql_client(aiohttp_client, myapp):
    yield GraphQLTestClient(aiohttp_client(myapp))
```

And use it everywere in your test methods

```python
def test_strawberry(graphql_client):
    query = """
        query Hi($name: String!) {
            hi(name: $name)
        }
    """

    result = graphql_client.query(query, variables={"name": "🍓"})

    assert result.data == {"hi": "Hi 🍓!"}
```

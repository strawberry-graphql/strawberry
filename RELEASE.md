Release type: minor

This release adds a `GraphQLTestClient` for Django. It hides the http request's details and asserts that there are no errors in the response (you can always disable this behavior by passing `asserts_errors=False`). This makes it easier to test queries and makes your tests cleaner.

If you are using `pytest` you can add a fixture in `conftest.py`

```python
import pytest

from django.test.client import Client

from strawberry.django.test import GraphQLTestClient


@pytest.fixture()
def graphql_client():
    yield GraphQLTestClient(Client())
```

And use it everywere in your test methods

```
def test_strawberry(graphql_client):
    query = """
        query Hi($name: String!) {
            hi(name: $name)
        }
    """

    result = graphql_client.query(query, variables={"name": "Marcotte"})

    assert result.data == {"hi": "Hi Marcotte!"}
```

---
title: Testing
---

# Testing

The GraphiQL playground integrated with Strawberry available at
[http://localhost:8000/graphql](http://localhost:8000/graphql) (if you run the schema
with `strawberry server`) can be a good place to start testing your queries and
mutations. However, at some point, while you are developing your application (or even
before if you are practising Test Driven Development), you may want to create some
automated tests.

We can use the Strawberry `schema` object we defined in the
[Getting Started tutorial](../index.md#step-5-create-our-schema-and-run-it) to run our
first test:

```python
def test_query():
    query = """
        query TestQuery($title: String!) {
            books(title: $title) {
                title
                author
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={"title": "The Great Gatsby"},
    )

    assert result.errors is None
    assert result.data["books"] == [
        {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
        }
    ]
```

This `test_query` example:

1. defines the query we will test against; it accepts one argument, `title`, as input
2. executes the query and assigns the result to a `result` variable
3. asserts that the result is what we are expecting: nothing in `errors` and our desired
   book in `data`

As you may have noticed, we explicitly defined the query variable `title`, and we passed
it separately with the `variable_values` argument, but we could have directly hardcoded
the `title` in the query string instead. We did this on purpose because usually the
query's arguments will be dynamic and, as we want to test our application as close to
production as possible, it wouldn't make much sense to hardcode the variables in the
query.

## Testing Async

Since Strawberry supports async, tests can also be written to be async:

```python
@pytest.mark.asyncio
async def test_query_async():
    ...

    resp = await schema.execute(query, variable_values={"title": "The Great Gatsby"})

    ...
```

## Testing Mutations

We can also write a test for our [`addBook` Mutation](../general/mutations.md) example:

```python
@pytest.mark.asyncio
async def test_mutation():
    mutation = """
        mutation TestMutation($title: String!, $author: String!) {
            addBook(title: $title, author: $author) {
                title
            }
        }
    """

    resp = await schema.execute(
        mutation,
        variable_values={
            "title": "The Little Prince",
            "author": "Antoine de Saint-Exupéry",
        },
    )

    assert resp.errors is None
    assert resp.data["addBook"] == {
        "title": "The Little Prince",
    }
```

## Testing Subscriptions

And finally, a test for our [`count` Subscription](../general/subscriptions.md):

```python
import asyncio
import pytest
import strawberry

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> int:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)

@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return "world"

schema = strawberry.Schema(query=Query, subscription=Subscription)

@pytest.mark.asyncio
async def test_subscription():
    query = """
    	subscription {
        	count(target: 3)
    	}
    """

    sub = await schema.subscribe(query)

    index = 0
    async for result in sub:
        assert not result.errors
        assert result.data == {"count": index}

        index += 1
```

As you can see testing Subscriptions is a bit more complicated because we want to check
the result of each individual result.

## Testing with API Client

To test the http request you can use our test client `GraphQLTestClient`. It hides the
http request's details and asserts that there are no errors in the response (you can
always disable this behavior by passing `asserts_errors=False` to the `query` method).
This makes it easier to test queries and makes your tests cleaner.

### Instantiate the `GraphQLTestClient`

We can start instantiating the `GraphQLTestClient` and, if you are using `pytest`, you
can add a fixture in `conftest.py`.

There are a different `GraphQLTestClient`s depending on the integration we use in our
application. The API is the same you just need to change the import.

#### With Django

```python
import pytest

from django.test.client import Client

from strawberry.django.test import GraphQLTestClient


@pytest.fixture()
def graphql_client():
    yield GraphQLTestClient(Client())
```

#### With asgi

```python
import pytest

from starlette.testclient import TestClient

from strawberry.asgi.test import GraphQLTestClient
from tests.asgi.app import create_app


@pytest.fixture
def test_client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def graphql_client(test_client):
    yield GraphQLTestClient(test_client)
```

#### With aiohttp

```python
import pytest

import pytest_asyncio

from strawberry.aiohttp.test.client import GraphQLTestClient
from tests.aiohttp.app import create_app


@pytest_asyncio.fixture
async def aiohttp_app_client(event_loop, aiohttp_client):
    app = create_app(graphiql=True)
    event_loop.set_debug(True)
    return await aiohttp_client(app)


@pytest.fixture
def graphql_client(aiohttp_app_client):
    yield GraphQLTestClient(aiohttp_app_client, url="/graphql")
```

### Define the tests with the `graphql_client` fixture

Finally, our tests will look like these:

```python
def test_strawberry(graphql_client):
    query = """
        query Hi($name: String!) {
            hi(name: $name)
        }
    """

    result = graphql_client.query(query, variables={"name": "Marcotte"})

    assert result.data == {"hi": "Hi Marcotte!"}


def test_fails(graphql_client):
    query = """
        query {
            nope
        }
    """

    result = graphql_client.query(query, asserts_errors=False)

    assert result.errors == []
```

### Testing file Upload

As Strawberry supports multipart uploads, we can test them with the test client as well.
We just have to add `files` parameter when we execute the query. Check the
[file upload](../guides/file-upload.md) documentation to understand how if works.

```python
from django.core.files.uploadedfile import SimpleUploadedFile

def test_upload(graphql_client):
    f = SimpleUploadedFile("file.txt", b"strawberry")
    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    response = graphql_client.query(
        query=query,
        variables={"textFile": None},
        files={"textFile": f},
    )

    assert response.data["readText"] == "strawberry"
```

---
title: Testing
---

# Testing

The GraphiQL playground integrated with Strawberry available at
[http://localhost:8000/graphql](http://localhost:8000/graphql) can be a good place to
start testing your queries and mutations. But at some point, while you are developing
your application (or even before if you are practising TDD), you may want to write down
also some automatic tests.

In order to test our queries, we must send an HTTP request to our "/graphql" endpoint,
so let's write a little client that helps us executing requests and hides some annoying
http details.

```
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Response:
    errors: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]


class GraphQLClient:
    def __init__(self, client):
        self._client = client

    def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Response:
        body = {"query": query}

        if variables:
            body["variables"] = variables

        resp = self._client.post("http://0.0.0.0:8000/graphql", json=body)
        data = json.loads(resp.content.decode())
        return Response(errors=data.get("errors"), data=data.get("data"))
```

We can also define a fixture (if you are using pytest) or a little function to avoid
initialising the GraphQLClient in every test.

Please note that we are using `requests` here, but if the framework you are using
includes a test client, you may want to use that instead and change the endpoint
accordingly.

```
import requests
import pytest

@pytest.fixture
def graphql_client():
    yield GraphQLClient(requests)
```

And here there is our test:

```
def test_query(graphql_client):
    query = """
        query($title: String!){
            books(title: $title){
                title
                author
            }
        }
    """

    resp = graphql_client.execute(query, variables={"title": "The Great Gatsby"})

    assert resp.errors is None
    assert resp.data["books"] == [
        {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
        }
    ]
```

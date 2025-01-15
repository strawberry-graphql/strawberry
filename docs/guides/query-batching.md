---
title: Query Batching
---

# Query Batching

Query batching is a feature in Strawberry GraphQL that allows clients to send
multiple queries, mutations, or a combination of both in a single HTTP request.
This can help optimize network usage and improve performance for applications
that make frequent GraphQL requests.

This document explains how to enable query batching, its configuration options,
and how to integrate it into your application with an example using FastAPI.

---

## Enabling Query Batching

To enable query batching in Strawberry, you need to configure the
`StrawberryConfig` when defining your GraphQL schema. The batching configuration
is provided as a dictionary with the key `enabled`:

```python
from strawberry.schema.config import StrawberryConfig

config = StrawberryConfig(batching_config={"enabled": True})
```

When batching is enabled, the server can handle a list of operations
(queries/mutations) in a single request and return a list of responses.

## Example Integration with FastAPI

Query Batching is supported on all Strawberry GraphQL framework integrations.
Below is an example of how to enable query batching in a FastAPI application:

```python
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(
    Query, config=StrawberryConfig(batching_config={"enabled": True})
)

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

### Running the Application

1.Save the code in a file (e.g., app.py). 2. Start the FastAPI server:
`bash     uvicorn app:app --reload     ` 3.The GraphQL endpoint will be
available at http://127.0.0.1:8000/graphql.

### Testing Query Batching

You can test query batching by sending a single HTTP request with multiple
GraphQL operations. For example:

#### Request

```bash
curl -X POST -H "Content-Type: application/json" \
-d '[{"query": "{ hello }"}, {"query": "{ hello }"}]' \
http://127.0.0.1:8000/graphql
```

#### Response

```json
[{ "data": { "hello": "Hello World" } }, { "data": { "hello": "Hello World" } }]
```

### Error Handling

#### Batching Disabled

If batching is not enabled in the server configuration and a batch request is
sent, the server will respond with a 400 status code and an error message:

```json
{
  "error": "Batching is not enabled"
}
```

#### Too Many Operations

If the number of operations in a batch exceeds the max_operations limit, the
server will return a 400 status code and an error message:

```json
{
  "error": "Too many operations"
}
```

### Limitations

#### Multipart Subscriptions:

Query batching does not support multipart subscriptions. Attempting to batch
such operations will result in a 400 error with a relevant message.

### Additional Notes

Query batching is particularly useful for clients that need to perform multiple
operations simultaneously, reducing the overhead of multiple HTTP requests.
Ensure your client library supports query batching before enabling it on the
server.

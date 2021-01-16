---
title: ASGI
---

# ASGI

Strawberry comes with a basic ASGI integration. It provides an app that you
can use to serve your GraphQL schema:

```python
from strawberry.asgi import GraphQL

from api.schema import Schema

app = GraphQL(schema)
```

## Options

The `GraphQL` app accepts two options at the moment:

- schema: mandatory, the schema created by `strawberry.Schema`.
- graphiql: optional, defaults to `True`, whether to enable the GraphiQL
  interface.

## Extending the view

We allow to extend the base `GraphQL` app, by overriding the following methods:

- `async get_context(self, request: Union[Request, WebSocket]) -> Any`
- `async get_root_value(self, request: Request) -> Any`
- `async process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`

## get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request.

```python
class MyGraphQL(GraphQL):
    async def get_context(self, request: Union[Request, WebSocket]) -> Any:
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info) -> str:
        return str(info.context["example"])
```

Here we are returning a custom context dictionary that contains only one item
called "example".

Then we use the context in a resolver, the resolver will return "1" in this
case.

## get_root_value

`get_root_value` allows to provide a custom root value for your schema, this is
probably not used a lot but it might be useful in certain situations.

Here's an example:

```python
class MyGraphQL(GraphQL):
    async def get_root_value(self, request: Request) -> Any:
        return Query(name="Patrick")


@strawberry.type
class Query:
    name: str
```

Here we are returning a Query where the name is "Patrick", so we when requesting
the field name we'll return "Patrick" in this case.

## process_result

`process_result` allows to customize and/or process results before they are sent
to the clients. This can be useful logging errors or hiding them (for example to
hide internal exceptions).

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and the execution results.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from graphql.error import format_error as format_graphql_error

class MyGraphQL(GraphQL):
    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [format_graphql_error(err) for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can
be tweaked based on your needs.

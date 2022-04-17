---
title: AIOHTTP
---

# AIOHTTP

Strawberry comes with a basic AIOHTTP integration. It provides a view that you
can use to serve your GraphQL schema:

```python
import strawberry
from aiohttp import web
from strawberry.aiohttp.views import GraphQLView


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: str = "World") -> str:
        return f"Hello, {name}!"


schema = strawberry.Schema(query=Query)

app = web.Application()

app.router.add_route("*", "/graphql", GraphQLView(schema=schema))
```

## Options

The `GraphQLView` accepts two options at the moment:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL
  interface.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests

## Extending the view

The base `GraphQLView` class can be extended by overriding the following
methods:

- `async get_context(self, request: aiohttp.web.Request, response: aiohttp.web.StreamResponse) -> object`
- `async get_root_value(self, request: aiohttp.web.Request) -> object`
- `async process_result(self, request: aiohttp.web.Request, result: ExecutionResult) -> GraphQLHTTPResponse`

## get_context

By overriding `GraphQLView.get_context` you can provide a custom context object
for your resolvers. You can return anything here; by default GraphQLView returns
a dictionary with the request.

```python
import strawberry
from aiohttp import web
from strawberry.types import Info
from strawberry.aiohttp.views import GraphQLView


class MyGraphQLView(GraphQLView):
    async def get_context(self, request: web.Request, response: web.StreamResponse):
        return {"request": request, "response": response, "example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: Info) -> str:
        return str(info.context["example"])
```

Here we are returning a custom context dictionary that contains only one item
called `"example"`.

Then we can use the context in a resolver. In this case the resolver will return
`1`.

## get_root_value

By overriding `GraphQLView.get_root_value` you can provide a custom root value
for your schema. This is probably not used a lot but it might be useful in
certain situations.

Here's an example:

```python
import strawberry
from aiohttp import web
from strawberry.aiohttp.views import GraphQLView


class MyGraphQLView(GraphQLView):
    async def get_root_value(self, request: web.Request):
        return Query(name="Patrick")


@strawberry.type
class Query:
    name: str
```

Here we configure a Query where requesting the `name` field will return
`"Patrick"` through the custom root value.

## process_result

By overriding `GraphQLView.process_result` you can customize and/or process
results before they are sent to a client. This can be useful for logging errors,
or even hiding them (for example to hide internal exceptions).

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and execution result.

```python
from aiohttp import web
from strawberry.aiohttp.views import GraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from graphql.error.graphql_error import format_error as format_graphql_error


class MyGraphQLView(GraphQLView):
    async def process_result(
        self, request: web.Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [format_graphql_error(err) for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

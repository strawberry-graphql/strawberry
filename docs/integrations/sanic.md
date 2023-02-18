---
title: Sanic
---

# Sanic

Strawberry comes with a basic [Sanic](https://github.com/sanic-org/sanic)
integration. It provides a view that you can use to serve your GraphQL schema:

```python
from strawberry.sanic.views import GraphQLView

from api.schema import Schema

app = Sanic(__name__)

app.add_route(
    GraphQLView.as_view(schema=schema, graphiql=True),
    "/graphql",
)
```

## Options

The `GraphQLView` accepts two options at the moment:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL
  interface.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests
- `def encode_json(self, data: GraphQLHTTPResponse) -> str`

## Extending the view

The base `GraphQLView` class can be extended by overriding the following
methods:

- `async get_context(self) -> Any`
- `get_root_value(self) -> Any`
- `process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse`

## get_context

By overriding `GraphQLView.get_context` you can provide a custom context object
for your resolvers. You can return anything here; by default GraphQLView returns
a dictionary with the request.

```python
class MyGraphQLView(GraphQLView):
    async def get_context(self, request) -> Any:
        return {"example": 1}


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
class MyGraphQLView(GraphQLView):
    def get_root_value(self) -> Any:
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

It needs to return an object of `GraphQLHTTPResponse` and accepts the execution
result.

```python
from strawberry.sanic.views import GraphQLView
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.types import ExecutionResult
from sanic.request import Request
from graphql.error.graphql_error import format_error as format_graphql_error


class MyGraphQLView(GraphQLView):
    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if result.errors:
            result.errors = [format_graphql_error(err) for err in result.errors]

        return process_result(data)
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

## encode_json

`encode_json` allows to customize the encoding of the JSON response. By default
we use `json.dumps` but you can override this method to use a different encoder.

```python
class MyGraphQLView(GraphQLView):
    def encode_json(self, data: GraphQLHTTPResponse) -> str:
        return json.dumps(data, indent=2)
```

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
- `json_encoder`: optional **JSON** encoder, defaults to `DjangoJSONEncoder`,
  will be used to serialize the data.
- `json_dumps_params`: optional dictionary of keyword arguments to pass to the
  `json.dumps` call used to generate the response. To get the most compact JSON
  representation, you should specify `{"separators": (",", ":")}`, defaults to
  `None`.

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
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from graphql.error.graphql_error import format_error as format_graphql_error

class MyGraphQLView(GraphQLView):
    def process_result(
        self, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [format_graphql_error(err) for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

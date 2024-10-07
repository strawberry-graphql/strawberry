---
title: Flask
---

# Flask

Strawberry comes with a basic Flask integration. It provides a view that you can
use to serve your GraphQL schema:

```python
from flask import Flask
from strawberry.flask.views import GraphQLView

from api.schema import schema

app = Flask(__name__)

app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view("graphql_view", schema=schema),
)

if __name__ == "__main__":
    app.run()
```

If you'd prefer to use an asynchronous view you can instead use the following
import which has the same interface as `GraphQLView`. This is helpful if using a
dataloader.

```python
from strawberry.flask.views import AsyncGraphQLView
```

## Options

The `GraphQLView` accepts the following options at the moment:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphql_ide`: optional, defaults to `"graphiql"`, allows to choose the
  GraphQL IDE interface (one of `graphiql`, `apollo-sandbox` or `pathfinder`) or
  to disable it by passing `None`.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests
- `multipart_uploads_enabled`: optional, defaults to `False`, controls whether
  to enable multipart uploads. Please make sure to consider the
  [security implications mentioned in the GraphQL Multipart Request Specification](https://github.com/jaydenseric/graphql-multipart-request-spec/blob/master/readme.md#security)
  when enabling this feature.

## Extending the view

We allow to extend the base `GraphQLView`, by overriding the following methods:

- `def get_context(self, request: Request, response: Response) -> Any`
- `def get_root_value(self, request: Request) -> Any`
- `def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def encode_json(self, response_data: GraphQLHTTPResponse) -> str`
- `def render_graphql_ide(self, request: Request) -> Response`

<Note>

Note that the `AsyncGraphQLView` can also be extended by overriding the same
methods above, but `get_context`, `get_root_value` and `process_result` are
async functions.

</Note>

### get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request. By default; the `Response` object from `flask` is injected via the
parameters.

```python
class MyGraphQLView(GraphQLView):
    def get_context(self, request: Request, response: Response) -> Any:
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        return str(info.context["example"])
```

Here we are returning a custom context dictionary that contains only one item
called "example".

Then we use the context in a resolver, the resolver will return "1" in this
case.

### get_root_value

`get_root_value` allows to provide a custom root value for your schema, this is
probably not used a lot but it might be useful in certain situations.

Here's an example:

```python
class MyGraphQLView(GraphQLView):
    def get_root_value(self, request: Request) -> Any:
        return Query(name="Patrick")


@strawberry.type
class Query:
    name: str
```

Here we are returning a Query where the name is "Patrick", so we when requesting
the field name we'll return "Patrick" in this case.

### process_result

`process_result` allows to customize and/or process results before they are sent
to the clients. This can be useful logging errors or hiding them (for example to
hide internal exceptions).

It needs to return an object of `GraphQLHTTPResponse` and accepts the execution
result.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult


class MyGraphQLView(GraphQLView):
    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [err.formatted for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

### encode_json

`encode_json` allows to customize the encoding of the JSON response. By default
we use `json.dumps` but you can override this method to use a different encoder.

```python
class MyGraphQLView(GraphQLView):
    def encode_json(self, data: GraphQLHTTPResponse) -> str:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
from strawberry.flask.views import GraphQLView
from flask import Request, Response


class MyGraphQLView(GraphQLView):
    def render_graphql_ide(self, request: Request) -> Response:
        custom_html = """<html><body><h1>Custom GraphQL IDE</h1></body></html>"""

        return Response(custom_html, status=200, content_type="text/html")
```

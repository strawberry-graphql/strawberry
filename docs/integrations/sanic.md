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

The base `GraphQLView` class can be extended by overriding any of the following
methods:

- `async def get_context(self, request: Request, response: TemporalResponse) -> Context`
- `async def get_root_value(self, request: Request) -> Optional[RootValue]`
- `async def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def decode_json(self, data: Union[str, bytes]) -> object`
- `def encode_json(self, data: object) -> str`
- `async def render_graphql_ide(self, request: Request) -> HTTPResponse`

### get_context

By overriding `GraphQLView.get_context` you can provide a custom context object
for your resolvers. You can return anything here; by default GraphQLView returns
a dictionary with the request.

```python
import strawberry
from strawberry.sanic.views import GraphQLView
from strawberry.http.temporal_response import TemporalResponse
from sanic.request import Request


class MyGraphQLView(GraphQLView):
    async def get_context(self, request: Request, response: TemporalResponse):
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        return str(info.context["example"])
```

Here we are returning a custom context dictionary that contains only one item
called `"example"`.

Then we can use the context in a resolver. In this case the resolver will return
`1`.

### get_root_value

By overriding `GraphQLView.get_root_value` you can provide a custom root value
for your schema. This is probably not used a lot but it might be useful in
certain situations.

Here's an example:

```python
import strawberry
from strawberry.sanic.views import GraphQLView
from sanic.request import Request


class MyGraphQLView(GraphQLView):
    async def get_root_value(self, request: Request):
        return Query(name="Patrick")


@strawberry.type
class Query:
    name: str
```

Here we configure a Query where requesting the `name` field will return
`"Patrick"` through the custom root value.

### process_result

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


class MyGraphQLView(GraphQLView):
    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if result.errors:
            result.errors = [err.formatted for err in result.errors]

        return process_result(data)
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

### decode_json

`decode_json` allows to customize the decoding of HTTP JSON requests. By default
we use `json.loads` but you can override this method to use a different decoder.

```python
from strawberry.sanic.views import GraphQLView
from typing import Union
import orjson


class MyGraphQLView(GraphQLView):
    def decode_json(self, data: Union[str, bytes]) -> object:
        return orjson.loads(data)
```

Make sure your code raises `json.JSONDecodeError` or a subclass of it if the
JSON cannot be decoded. The library shown in the example above, `orjson`, does
this by default.

### encode_json

`encode_json` allows to customize the encoding of HTTP and WebSocket JSON
responses. By default we use `json.dumps` but you can override this method to
use a different encoder.

```python
import json
from strawberry.sanic.views import GraphQLView


class MyGraphQLView(GraphQLView):
    def encode_json(self, data: object) -> str:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
from strawberry.sanic.views import GraphQLView
from sanic.request import Request
from sanic.response import HTTPResponse, html


class MyGraphQLView(GraphQLView):
    async def render_graphql_ide(self, request: Request) -> HTTPResponse:
        custom_html = """<html><body><h1>Custom GraphQL IDE</h1></body></html>"""

        return html(custom_html)
```

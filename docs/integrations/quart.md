---
title: Quart
---

# Quart

Strawberry comes with a basic Quart integration. It provides a view that you can
use to serve your GraphQL schema:

```python
from quart import Quart
from strawberry.quart.views import GraphQLView
from api.schema import schema

view = GraphQLView.as_view("graphql_view", schema=schema)

app = Quart(__name__)
app.add_url_rule("/graphql", view_func=view)
app.add_url_rule("/graphql", view_func=view, methods=["GET"], websocket=True)

if __name__ == "__main__":
    app.run()
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

- `async def get_context(self, request: Request, response: Response) -> Context`
- `async def get_root_value(self, request: Request) -> Optional[RootValue]`
- `async def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def decode_json(self, data: Union[str, bytes]) -> object`
- `def encode_json(self, data: object) -> str | bytes`
- `async def render_graphql_ide(self, request: Request) -> Response`
- `async def on_ws_connect(self, context: Context) -> Union[UnsetType, None, Dict[str, object]]`

### get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request. By default; the `Response` object from Quart is injected via the
parameters.

```python
import strawberry
from strawberry.quart.views import GraphQLView
from quart import Request, Response


class MyGraphQLView(GraphQLView):
    async def get_context(self, request: Request, response: Response):
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
import strawberry
from strawberry.quart.views import GraphQLView
from quart import Request


class MyGraphQLView(GraphQLView):
    async def get_root_value(self, request: Request):
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
from strawberry.quart.views import GraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from quart import Request


class MyGraphQLView(GraphQLView):
    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [err.formatted for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

### decode_json

`decode_json` allows to customize the decoding of HTTP JSON requests. By default
we use `json.loads` but you can override this method to use a different decoder.

```python
from strawberry.quart.views import GraphQLView
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
from strawberry.quart.views import GraphQLView


class MyGraphQLView(GraphQLView):
    def encode_json(self, data: object) -> str | bytes:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
from strawberry.quart.views import GraphQLView
from quart import Request, Response


class MyGraphQLView(GraphQLView):
    async def render_graphql_ide(self, request: Request) -> Response:
        custom_html = """<html><body><h1>Custom GraphQL IDE</h1></body></html>"""

        return Response(custom_html)
```

### on_ws_connect

By overriding `on_ws_connect` you can customize the behavior when a `graphql-ws`
or `graphql-transport-ws` connection is established. This is particularly useful
for authentication and authorization. By default, all connections are accepted.

To manually accept a connection, return `strawberry.UNSET` or a connection
acknowledgment payload. The acknowledgment payload will be sent to the client.

Note that the legacy protocol does not support `None`/`null` acknowledgment
payloads, while the new protocol does. Our implementation will treat
`None`/`null` payloads the same as `strawberry.UNSET` in the context of the
legacy protocol.

To reject a connection, raise a `ConnectionRejectionError`. You can optionally
provide a custom error payload that will be sent to the client when the legacy
GraphQL over WebSocket protocol is used.

```python
from typing import Dict
from strawberry.exceptions import ConnectionRejectionError
from strawberry.quart.views import GraphQLView


class MyGraphQLView(GraphQLView):
    async def on_ws_connect(self, context: Dict[str, object]):
        connection_params = context["connection_params"]

        if not isinstance(connection_params, dict):
            # Reject without a custom graphql-ws error payload
            raise ConnectionRejectionError()

        if connection_params.get("password") != "secret":
            # Reject with a custom graphql-ws error payload
            raise ConnectionRejectionError({"reason": "Invalid password"})

        if username := connection_params.get("username"):
            # Accept with a custom acknowledgment payload
            return {"message": f"Hello, {username}!"}

        # Accept without an acknowledgment payload
        return await super().on_ws_connect(context)
```

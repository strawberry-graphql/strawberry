---
title: ASGI
---

# ASGI

Strawberry comes with a basic ASGI integration. It provides an app that you can
use to serve your GraphQL schema. Before using Strawberry's ASGI support make
sure you install all the required dependencies by running:

```shell
pip install 'strawberry-graphql[asgi]'
```

Once that's done you can use Strawberry with ASGI like so:

```python
# server.py
from strawberry.asgi import GraphQL

from api.schema import schema

app = GraphQL(schema)
```

Every ASGI server will accept this `app` instance to start the server. For
example if you're using [uvicorn](https://pypi.org/project/uvicorn/) you run the
app with `uvicorn server:app`

## Options

The `GraphQL` app accepts the following options at the moment:

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

The base `GraphQL` class can be extended by overriding any of the following
methods:

- `async def get_context(self, request: Union[Request, WebSocket], response: Union[Response, WebSocket]) -> Context`
- `async def get_root_value(self, request: Union[Request, WebSocket]) -> Optional[RootValue]`
- `async def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def decode_json(self, data: Union[str, bytes]) -> object`
- `def encode_json(self, data: object) -> str`
- `async def render_graphql_ide(self, request: Request) -> Response`

### get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request and the response.

```python
import strawberry
from typing import Union
from strawberry.asgi import GraphQL
from starlette.requests import Request
from starlette.responses import Response


class MyGraphQL(GraphQL):
    async def get_context(
        self, request: Union[Request, WebSocket], response: Optional[Response] = None
    ):
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

#### Setting response headers

It is possible to use `get_context` to set response headers. A common use case
might be cookie-based user authentication, where your login mutation resolver
needs to set a cookie on the response.

This is possible by updating the response object contained inside the context of
the `Info` object.

```python
import strawberry


@strawberry.type
class Mutation:
    @strawberry.mutation
    def login(self, info: strawberry.Info) -> bool:
        token = do_login()
        info.context["response"].set_cookie(key="token", value=token)
        return True
```

#### Setting background tasks

Similarly, [background tasks](https://www.starlette.io/background/) can be set
on the response via the context:

```python
import strawberry
from starlette.background import BackgroundTask


async def notify_new_flavour(name: str): ...


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_flavour(self, name: str, info: strawberry.Info) -> bool:
        info.context["response"].background = BackgroundTask(notify_new_flavour, name)
```

### get_root_value

`get_root_value` allows to provide a custom root value for your schema, this is
probably not used a lot but it might be useful in certain situations.

Here's an example:

```python
import strawberry
from typing import Union
from strawberry.asgi import GraphQL
from starlette.requests import Request
from starlette.websockets import WebSocket


class MyGraphQL(GraphQL):
    async def get_root_value(self, request: Union[Request, WebSocket]):
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

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and the execution results.

```python
from strawberry.asgi import GraphQL
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from starlette.requests import Request


class MyGraphQL(GraphQL):
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
from strawberry.asgi import GraphQL
from typing import Union
import orjson


class MyGraphQLView(GraphQL):
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
from strawberry.asgi import GraphQL


class MyGraphQLView(GraphQL):
    def encode_json(self, data: object) -> str:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
from strawberry.asgi import GraphQL
from starlette.responses import HTMLResponse, Response


class MyGraphQL(GraphQL):
    async def render_graphql_ide(self, request: Request) -> Response:
        custom_html = """<html><body><h1>Custom GraphQL IDE</h1></body></html>"""

        return HTMLResponse(custom_html)
```

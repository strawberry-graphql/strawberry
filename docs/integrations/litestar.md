---
title: Litestar
---

# Litestar

Strawberry comes with an integration for [Litestar](https://litestar.dev/) by
providing a `make_graphql_controller` function that can be used to create a
GraphQL controller.

See the example below for integrating Litestar with Strawberry:

```python
import strawberry
from litestar import Litestar
from strawberry.litestar import make_graphql_controller


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
)

app = Litestar(route_handlers=[GraphQLController])
```

## Options

The `make_graphql_controller` function accepts the following options:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `path`: optional, defaults to ``, the path where the GraphQL endpoint will be
  mounted.
- `graphql_ide`: optional, defaults to `"graphiql"`, allows to choose the
  GraphQL IDE interface (one of `graphiql`, `apollo-sandbox` or `pathfinder`) or
  to disable it by passing `None`.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests
- `context_getter`: optional Litestar dependency for providing custom context
  value.
- `root_value_getter`: optional Litestar dependency for providing custom root
  value.
- `debug`: optional, defaults to `False`, whether to enable debug mode.
- `keep_alive`: optional, defaults to `False`, whether to enable keep alive mode
  for websockets.
- `keep_alive_interval`: optional, defaults to `1`, the interval in seconds for
  keep alive messages.
- `subscription_protocols` optional, defaults to
  `(GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL)`, the allowed
  subscription protocols
- `connection_init_wait_timeout` optional, default to `timedelta(minutes=1)`,
  the maximum time to wait for the connection initialization message when using
  `graphql-transport-ws`
  [protocol](https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md#connectioninit)
- `multipart_uploads_enabled`: optional, defaults to `False`, controls whether
  to enable multipart uploads. Please make sure to consider the
  [security implications mentioned in the GraphQL Multipart Request Specification](https://github.com/jaydenseric/graphql-multipart-request-spec/blob/master/readme.md#security)
  when enabling this feature.

### context_getter

The `context_getter` option allows you to provide a Litestar dependency that
return a custom context object that can be used in your resolver.

```python
import strawberry
from litestar import Request, Litestar
from strawberry.litestar import make_graphql_controller
from strawberry.types.info import Info


async def custom_context_getter():
    return {"custom": "context"}


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info: strawberry.Info[dict, None]) -> str:
        return info.context["custom"]


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=custom_context_getter,
)

app = Litestar(route_handlers=[GraphQLController])
```

The `context_getter` is a standard Litestar dependency and can receive any
existing dependency:

```python
import strawberry
from litestar import Request, Litestar
from strawberry.litestar import make_graphql_controller
from strawberry.types.info import Info
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from sqlalchemy import select


async def custom_context_getter(request: Request, db_session: AsyncSession):
    return {"user": request.user, "session": db_session}


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self, info: strawberry.Info[dict, None]) -> str:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"]

        query = select(User).where(User.id == user.id)
        user = (await session.execute((query))).scalar_one()
        return f"Hello {user.first_name}"


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=custom_context_getter,
)

app = Litestar(route_handlers=[GraphQLController])
```

You can also use a class-based custom context. To do this, you must inherit from
`BaseContext` [msgspec Struct](https://jcristharif.com/msgspec/structs.html) or
an `InvalidCustomContext` exception will be raised.

```python
import strawberry
from litestar import Request, Litestar
from strawberry.litestar import make_graphql_controller, BaseContext
from strawberry.types.info import Info
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from sqlalchemy import select


class CustomContext(BaseContext):
    user: User
    session: AsyncSession


async def custom_context_getter(
    request: Request, db_session: AsyncSession
) -> CustomContext:
    return CustomContext(user=request.user, session=db_session)


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self, info: strawberry.Info[CustomContext, None]) -> str:
        session: AsyncSession = info.context.session
        user: User = info.context.user

        query = select(User).where(User.id == user.id)
        user = (await session.execute((query))).scalar_one()
        return f"Hello {user.first_name}"


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=custom_context_getter,
)

app = Litestar(route_handlers=[GraphQLController])
```

#### Context typing

In our previous example using class based context, the actual runtime context a
`CustomContext` type. Because it inherits from `BaseContext`, the `request`,
`socket` and `response` attributes are typed as optional.

When inside a query/mutation resolver, `request` and `response` are always set
and `socket` is only set in subscriptions.

To distinguish theses cases typing wise, the integration provides two classes
that will help you to enforce strong typing:

```python
from strawberry.litestar import HTTPContextType, WebSocketContextType
```

These classes does not actually exists at runtime, they are intended to be used
to define a custom `Info` type with proper context typing. Taking over our
previous example with class based custom context, here it how we can define two
`Info` types for both queries/mutations and subscriptions:

```python
import strawberry
from typing import Any
from litestar import Request, Litestar
from litestar.datastructures import State
from strawberry.litestar import (
    make_graphql_controller,
    BaseContext,
    HTTPContextType,
    WebSocketContextType,
)
from strawberry.types.info import Info
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from sqlalchemy import select


class CustomContext(BaseContext, kw_only=True):
    user: User
    session: AsyncSession


class CustomHTTPContextType(HTTPContextType, CustomContext):
    request: Request[User, Any, State]


class CustomWSContextType(WebSocketContextType, CustomContext):
    socket: WebSocket[User, Token, State]


async def custom_context_getter(
    request: Request, db_session: AsyncSession
) -> CustomContext:
    return CustomContext(user=request.user, session=db_session)


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self, info: strawberry.Info[CustomHTTPContextType, None]) -> str:
        session: AsyncSession = info.context.session
        user: User = info.context.user

        query = select(User).where(User.id == user.id)
        user = (await session.execute((query))).scalar_one()
        return f"Hello {user.first_name}"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(
        self, info: strawberry.Info[CustomWSContextType, None], target: int = 100
    ) -> AsyncGenerator[int, None]:
        import devtools

        devtools.debug(info.context)
        devtools.debug(info.context.socket)
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)


schema = strawberry.Schema(Query, subscription=Subscription)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=custom_context_getter,
)

app = Litestar(route_handlers=[GraphQLController])
```

### root_value_getter

The `root_value_getter` option allows you to provide a custom root value that
can be used in your resolver

```python
import strawberry
from litestar import Request, Litestar
from strawberry.litestar import make_graphql_controller


@strawberry.type
class Query:
    example: str = "Hello World"

    @strawberry.field
    def hello(self) -> str:
        return self.example


def custom_get_root_value():
    return Query()


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    root_value_getter=custom_get_root_value,
)

app = Litestar(route_handlers=[GraphQLController])
```

## Extending the controller

The base `GraphQLController` class returned by `make_graphql_controller` can be
extended by overriding any of the following methods:

- `async def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def decode_json(self, data: Union[str, bytes]) -> object`
- `def encode_json(self, data: object) -> str`
- `async def render_graphql_ide(self, request: Request) -> Response`
- `async def on_ws_connect(self, context: Context) -> Union[UnsetType, None, Dict[str, object]]`

### process_result

The `process_result` option allows you to customize and/or process results
before they are sent to the clients. This can be useful for logging errors or
hiding them (for example to hide internal exceptions).

It needs to return a `GraphQLHTTPResponse` object and accepts the request and
execution results.

```python
import strawberry
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from strawberry.litestar import make_graphql_controller
from litestar import Request


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
)


class MyGraphQLController(GraphQLController):
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

`decode_json` allows to customize the decoding of HTTP and WebSocket JSON
requests. By default we use `json.loads` but you can override this method to use
a different decoder.

```python
import strawberry
import orjson
from strawberry.litestar import make_graphql_controller
from typing import Union


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
)


class MyGraphQLController(GraphQLController):
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
import strawberry
from strawberry.litestar import make_graphql_controller


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
)


class MyGraphQLController(GraphQLController):
    def encode_json(self, data: object) -> bytes:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
import strawberry
from strawberry.litestar import make_graphql_controller
from litestar import MediaType, Request, Response


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
)


class MyGraphQLController(GraphQLController):
    async def render_graphql_ide(self, request: Request) -> Response:
        custom_html = """<html><body><h1>Custom GraphQL IDE</h1></body></html>"""

        return Response(custom_html, media_type=MediaType.HTML)
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
import strawberry
from typing import Dict
from strawberry.exceptions import ConnectionRejectionError
from strawberry.litestar import make_graphql_controller


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


schema = strawberry.Schema(Query)

GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
)


class MyGraphQLController(GraphQLController):
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

        # Accept without a acknowledgment payload
        return await super().on_ws_connect(context)
```

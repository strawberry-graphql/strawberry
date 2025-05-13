---
title: FastAPI
---

# FastAPI

Strawberry provides support for [FastAPI](https://fastapi.tiangolo.com/) with a
custom
[APIRouter](https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter)
called `GraphQLRouter`.

Before using Strawberry's FastAPI support make sure you install all the required
dependencies by running:

```shell
pip install 'strawberry-graphql[fastapi]'
```

See the example below for integrating FastAPI with Strawberry:

```python
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

<Note>

Both FastAPI and Strawberry support sync and async functions, but their behavior
is different.

FastAPI processes sync endpoints in a threadpool and async endpoints using the
event loop. However, Strawberry processes sync and async fields using the event
loop, which means that using a sync `def` will block the entire worker.

It is recommended to use `async def` for all of your fields if you want to be
able to handle concurrent request on a single worker. If you can't use async,
make sure you wrap blocking code in a suspending thread, for example using
`starlette.concurrency.run_in_threadpool`.

</Note>

## Options

The `GraphQLRouter` accepts the following options:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphql_ide`: optional, defaults to `"graphiql"`, allows to choose the
  GraphQL IDE interface (one of `graphiql`, `apollo-sandbox` or `pathfinder`) or
  to disable it by passing `None`.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests
- `context_getter`: optional FastAPI dependency for providing custom context
  value.
- `root_value_getter`: optional FastAPI dependency for providing custom root
  value.
- `multipart_uploads_enabled`: optional, defaults to `False`, controls whether
  to enable multipart uploads. Please make sure to consider the
  [security implications mentioned in the GraphQL Multipart Request Specification](https://github.com/jaydenseric/graphql-multipart-request-spec/blob/master/readme.md#security)
  when enabling this feature.

### context_getter

The `context_getter` option allows you to provide a custom context object that
can be used in your resolver. `context_getter` is a
[FastAPI dependency](https://fastapi.tiangolo.com/tutorial/dependencies/) and
can inject other dependencies if you so wish.

There are two options at your disposal here:

1. Define your custom context as a dictionary,
2. Define your custom context as a class.

If no context is supplied, then the default context returned is a dictionary
containing the request, the response, and any background tasks.

However, you can define a class-based custom context inline with
[FastAPI practice](https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/).
If you choose to do this, you must ensure that your custom context class
inherits from `BaseContext` or an `InvalidCustomContext` exception is raised.

For dictionary-based custom contexts, an example might look like the following.

```python
import strawberry

from fastapi import FastAPI, Depends, Request, WebSocket, BackgroundTasks
from strawberry.fastapi import GraphQLRouter


def custom_context_dependency() -> str:
    return "John"


async def get_context(
    custom_value=Depends(custom_context_dependency),
):
    return {
        "custom_value": custom_value,
    }


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        return f"Hello {info.context['custom_value']}"


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

Here we are returning a custom context dictionary that contains one extra item
called "custom*value", which is injected from `custom_context_dependency`. This
value exists alongside `request`, `response`, and `background_tasks` in the
`info.context` \_dictionary* and so it requires `['request']` indexing.

Then we use the context in a resolver. The resolver will return "Hello John" in
this case.

For class-based custom contexts, an example might look like the following.

```python
import strawberry

from fastapi import FastAPI, Depends, Request, WebSocket, BackgroundTasks
from strawberry.fastapi import BaseContext, GraphQLRouter


class CustomContext(BaseContext):
    def __init__(self, greeting: str, name: str):
        self.greeting = greeting
        self.name = name


def custom_context_dependency() -> CustomContext:
    return CustomContext(greeting="you rock!", name="John")


async def get_context(
    custom_context=Depends(custom_context_dependency),
):
    return custom_context


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        return f"Hello {info.context.name}, {info.context.greeting}"


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

In this case, we are returning a custom context class that inherits from
BaseContext with fields `name` and `greeting`, which is also injected by
`custom_context_dependency`. These custom values exist alongside `request`,
`response`, and `background_tasks` in the `info.context` _class_ and so it
requires `.request` indexing.

Then we use the context in a resolver. The resolver will return “Hello John, you
rock!” in this case.

#### Setting background tasks

Similarly,
[background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/?h=background)
can be added via the context:

```python
import strawberry

from fastapi import FastAPI, BackgroundTasks
from strawberry.fastapi import GraphQLRouter


async def notify_new_flavour(name: str):
    print(name)


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_flavour(self, name: str, info: strawberry.Info) -> bool:
        info.context["background_tasks"].add_task(notify_new_flavour, name)
        return True


schema = strawberry.Schema(Query, Mutation)

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

If using a custom context class, then background tasks should be stored within
the class object as `.background_tasks`.

### root_value_getter

The `root_value_getter` option allows you to provide a custom root value for
your schema. This is most likely a rare usecase but might be useful in certain
situations.

Here's an example:

```python
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


async def get_root_value():
    return Query(name="Patrick")


@strawberry.type
class Query:
    name: str


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(
    schema,
    root_value_getter=get_root_value,
)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

Here we are returning a Query where the name is "Patrick", so when we request
the field name we'll return "Patrick".

## Extending the router

The base `GraphQLRouter` class can be extended by overriding any of the
following methods:

- `async def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def decode_json(self, data: Union[str, bytes]) -> object`
- `def encode_json(self, data: object) -> str`
- `async def render_graphql_ide(self, request: Request) -> HTMLResponse`
- `async def on_ws_connect(self, context: Context) -> Union[UnsetType, None, Dict[str, object]]`

### process_result

The `process_result` option allows you to customize and/or process results
before they are sent to the clients. This can be useful for logging errors or
hiding them (for example to hide internal exceptions).

It needs to return a `GraphQLHTTPResponse` object and accepts the request and
execution results.

```python
from starlette.requests import Request
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult


class MyGraphQLRouter(GraphQLRouter):
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
from strawberry.fastapi import GraphQLRouter
from typing import Union
import orjson


class MyGraphQLRouter(GraphQLRouter):
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
from strawberry.fastapi import GraphQLRouter
import json


class MyGraphQLRouter(GraphQLRouter):
    def encode_json(self, data: object) -> bytes:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
from strawberry.fastapi import GraphQLRouter
from starlette.responses import HTMLResponse, Response
from starlette.requests import Request


class MyGraphQLRouter(GraphQLRouter):
    async def render_graphql_ide(self, request: Request) -> HTMLResponse:
        custom_html = """<html><body><h1>Custom GraphQL IDE</h1></body></html>"""

        return HTMLResponse(custom_html)
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
from strawberry.fastapi import GraphQLRouter


class MyGraphQLRouter(GraphQLRouter):
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

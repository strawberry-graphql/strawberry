---
title: ASGI
---

# ASGI

Strawberry comes with a basic ASGI integration. It provides an app that you can
use to serve your GraphQL schema. Before using Strawberry's ASGI support make
sure you install all the required dependencies by running:

```
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

The `GraphQL` app accepts two options at the moment:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL
  interface.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests

## Extending the view

We allow to extend the base `GraphQL` app, by overriding the following methods:

- `async get_context(self, request: Union[Request, WebSocket], response: Optional[Response] = None) -> Any`
- `async get_root_value(self, request: Request) -> Any`
- `async process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`

## get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request and the response.

```python
class MyGraphQL(GraphQL):
    async def get_context(self, request: Union[Request, WebSocket], response: Optional[Response] = None) -> Any:
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: Info) -> str:
        return str(info.context["example"])
```

Here we are returning a custom context dictionary that contains only one item
called "example".

Then we use the context in a resolver, the resolver will return "1" in this
case.

### Setting response headers

It is possible to use `get_context` to set response headers. A common use case
might be cookie-based user authentication, where your login mutation resolver
needs to set a cookie on the response.

This is possible by updating the response object contained inside the context of
the `Info` object.

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    def login(self, info: Info) -> bool:
        token = do_login()
        info.context["response"].set_cookie(key="token", value=token)
        return True
```

### Setting background tasks

Similarly, [background tasks](https://www.starlette.io/background/) can be set
on the response via the context:

```python
from starlette.background import BackgroundTask

async def notify_new_flavour(name: str):
    ...

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_flavour(self, name: str, info: Info) -> bool:
        info.context["response"].background = BackgroundTask(notify_new_flavour, name)
```

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

from graphql.error.graphql_error import format_error as format_graphql_error

class MyGraphQL(GraphQL):
    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [format_graphql_error(err) for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

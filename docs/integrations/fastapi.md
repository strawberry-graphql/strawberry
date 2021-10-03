---
title: FastAPI
---

# FastAPI

Strawberry provides support for [FastAPI](https://fastapi.tiangolo.com/) with the APIRouter integration.

See below example for integrating FastAPI with Strawberry:

```python
from fastapi import FastAPI
from strawberry.fastapi import GraphQL

from api.schema import schema

graphql_app = GraphQL(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

## Options

The `GraphQL` app accepts following options:

- schema: mandatory, the schema created by `strawberry.Schema`.
- graphiql: optional, defaults to `True`, whether to enable the GraphiQL
  interface.
- context_getter: optional FastAPI dependency for prividing custom context value
- root_value_getter: optional FastAPI dependency for prividing custom root value

## context_getter

`context_getter` option allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request and background tasks.

`context_getter` is [FastAPI dependency](https://fastapi.tiangolo.com/tutorial/dependencies/)
and can inject another dependencies.

```python
from fastapi import Depends, Request, WebSocket, BackgroundTasks

def custom_context_dependency() -> str:
    return "Hi!"


async def get_context(
    background_tasks: BackgroundTasks,
    request: Request = None,
    ws: WebSocket = None,
    custom_value=Depends(custom_context_dependency),
):
    return {
        "custom_value": custom_value,
        "request": request or ws,
        "background_tasks": background_tasks,
    }


graphql_app = GraphQL(
  schema,
  context_getter=get_context
)

@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: Info) -> str:
        return str(info.context["custom_value"])
```

Here we are returning a custom context dictionary that contains one extra item
called "custom_value", which is injected from `custom_context_dependency`.

Then we use the context in a resolver, the resolver will return "Hi!" in this
case.

### Setting background tasks

Similarly, [background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/?h=background) can be added via the context:

```python
from starlette.background import BackgroundTask

async def notify_new_flavour(name: str):
    ...

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_flavour(self, name: str, info: Info) -> bool:
        info.context["background_tasks"].add_task(notify_new_flavour)

        info.context["response"].background = BackgroundTask(notify_new_flavour, name)
```

## root_value_getter

`root_value_getter` option allows to provide a custom root value for your schema, this is
probably not used a lot but it might be useful in certain situations.

Here's an example:

```python
from fastapi import Request

async def get_root_value(request: Request):
    return Query(name="Patrick")


graphql_app = GraphQL(
    schema,
    root_value_getter=get_root_value,
)

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

from graphql.error import format_error as format_graphql_error

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
tweaked based on your needs. the result, but it can be tweaked based on your needs.

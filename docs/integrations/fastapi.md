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

```
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

## Options

The `GraphQLRouter` accepts the following options:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL
  interface.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests
- `context_getter`: optional FastAPI dependency for providing custom context
  value.
- `root_value_getter`: optional FastAPI dependency for providing custom root
  value.

## context_getter

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
from strawberry.types import Info
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
    def example(self, info: Info) -> str:
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
from strawberry.types import Info
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
    def example(self, info: Info) -> str:
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

### Setting background tasks

Similarly,
[background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/?h=background)
can be added via the context:

```python
import strawberry

from fastapi import FastAPI, BackgroundTasks
from strawberry.types import Info
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
    def create_flavour(self, name: str, info: Info) -> bool:
        info.context["background_tasks"].add_task(notify_new_flavour, name)
        return True


schema = strawberry.Schema(Query, Mutation)

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

If using a custom context class, then background tasks should be stored within
the class object as `.background_tasks`.

## root_value_getter

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

## process_result

The `process_result` option allows you to customize and/or process results
before they are sent to the clients. This can be useful for logging errors or
hiding them (for example to hide internal exceptions).

It needs to return a `GraphQLHTTPResponse` object and accepts the request and
execution results.

```python
from fastapi import Request
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from graphql.error.graphql_error import format_error as format_graphql_error

class MyGraphQLRouter(GraphQLRouter):

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

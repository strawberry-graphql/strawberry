---
title: Litestar
---

# Litestar

Strawberry comes with an integration for
[Litestar](https://litestar.dev/) by providing a
`make_graphql_controller` function that can be used to create a GraphQL
controller.

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

app = Litestar(
    route_handlers=[GraphQLController],
)
```

## Options

The `make_graphql_controller` function accepts the following options:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `path`: optional, defaults to ``, the path where the GraphQL endpoint will be
  mounted.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL
  interface.
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

## context_getter

The `context_getter` option allows you to provide a custom context object that
can be used in your resolver. It receives a `request` object that can be used to
extract information from the request.

```python
import strawberry
from litestar import Request, Litestar
from strawberry.litestar import make_graphql_controller
from strawberry.types.info import Info


def custom_context_getter(request: Request):
    return {"custom": "context"}


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info: Info[object, None]) -> str:
        return info.context["custom"]


schema = strawberry.Schema(Query)


GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=custom_context_getter,
)

app = Litestar(
    route_handlers=[GraphQLController],
)
```

## root_value_getter

The `root_value_getter` option allows you to provide a custom root value that
can be used in your resolver. It receives a `request` object that can be used to
extract information from the request.

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


def custom_get_root_value(request: Request):
    return Query()


schema = strawberry.Schema(Query)


GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    root_value_getter=custom_get_root_value,
)

app = Litestar(
    route_handlers=[GraphQLController],
)
```

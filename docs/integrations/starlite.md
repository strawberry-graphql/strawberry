---
title: Starlite
---

# Starlite

## Deprecation Notice

This integration has been deprecated in favor of the `Litestar` integration.
Refer to the [Litestar](./litestar.md) integration for more information.
Litestar is a
[renamed](https://litestar.dev/about/organization.html#litestar-and-starlite)
and upgraded version of Starlite.

## How to use

Strawberry comes with an integration for
[Starlite](https://starliteproject.dev/) by providing a
`make_graphql_controller` function that can be used to create a GraphQL
controller.

See the example below for integrating Starlite with Strawberry:

```python
import strawberry
from starlite import Starlite
from strawberry.starlite import make_graphql_controller


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

app = Starlite(
    route_handlers=[GraphQLController],
)
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
- `context_getter`: optional Starlite dependency for providing custom context
  value.
- `root_value_getter`: optional Starlite dependency for providing custom root
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
from starlite import Request, Starlite
from strawberry.starlite import make_graphql_controller
from strawberry.types.info import Info


def custom_context_getter(request: Request):
    return {"custom": "context"}


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info: strawberry.Info[object, None]) -> str:
        return info.context["custom"]


schema = strawberry.Schema(Query)


GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=custom_context_getter,
)

app = Starlite(
    route_handlers=[GraphQLController],
)
```

## root_value_getter

The `root_value_getter` option allows you to provide a custom root value that
can be used in your resolver. It receives a `request` object that can be used to
extract information from the request.

```python
import strawberry
from starlite import Request, Starlite
from strawberry.starlite import make_graphql_controller


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

app = Starlite(
    route_handlers=[GraphQLController],
)
```

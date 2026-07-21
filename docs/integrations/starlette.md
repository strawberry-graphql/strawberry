---
title: Starlette
---

# Starlette

Strawberry provides support for [Starlette](https://www.starlette.io/) with the
ASGI integration.

Use `Route` and `WebSocketRoute` to integrate Strawberry with Starlette:

```python
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from strawberry.asgi import GraphQL

from api.schema import schema

graphql_app = GraphQL(schema)

app = Starlette(
    routes=[
        Route("/graphql", graphql_app),
        WebSocketRoute("/graphql", graphql_app),
    ]
)
```

For more information about Strawberry ASGI refer to
[the documentation on ASGI](./asgi.md)

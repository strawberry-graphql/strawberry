---
title: Starlette
---

# Starlette

Strawberry provides support for [Starlette](https://www.starlette.io/) with the
ASGI integration.

See below example for integrating Starlette with Strawberry:

```python
from starlette.applications import Starlette
from strawberry.asgi import GraphQL

from api.schema import schema

graphql_app = GraphQL(schema)

app = Starlette()
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)
```

For more information about Strawberry ASGI refer to
[the documentation on ASGI](./asgi.md)

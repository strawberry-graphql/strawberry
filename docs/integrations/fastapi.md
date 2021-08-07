---
title: FastAPI
---

# FastAPI

Strawberry provides support for [FastAPI](https://fastapi.tiangolo.com/) with the ASGI integration.

See below example for integrating FastAPI with Strawberry:

```python
from fastapi import FastAPI
from strawberry.asgi import GraphQL

from api.schema import Schema

graphql_app = GraphQL(schema)

app = FastAPI()
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/subscriptions", graphql_app)
```

For more information about Strawberry ASGI refer to [asgi.md](./asgi.md)

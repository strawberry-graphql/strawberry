---
title: FastAPI
---

# FastAPI

Strawberry comes with a [FastAPI](https://fastapi.tiangolo.com/) integration.
It provides a router that you can use to serve your GraphQL schema:

```python
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from api.schema import schema

app = FastAPI()
app.include_router(
    GraphQLRouter(schema, graphiql=True),
    prefix="/graphql",
    tags=["GraphQL"],
)
```

The integration is built as a shell around the Strawberry ASGI integration.
For more information about Strawberry ASGI refer to [asgi.md](./asgi.md)

---
title: FastAPI
---

# FastAPI

Strawberry comes with a [FastAPI](https://fastapi.tiangolo.com/) integration.
Install it using:
```console
pip install strawberry-graphql[fastapi]
```

It integrates with your FastAPI application using an APIRouter:
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
After which your GraphQL schema is exposed on the given `prefix`.

The integration is built as a shell around the Strawberry ASGI integration.
For more information about Strawberry ASGI refer to [asgi.md](./asgi.md)

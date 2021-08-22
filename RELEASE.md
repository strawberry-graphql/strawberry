Release type: minor

This release adds dedicated support for FastAPI.

Previously FastAPI was supported using the ASGI integration, this still works,
however the new intergration plays nicely with FastAPIs OpenAPI documentation.

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

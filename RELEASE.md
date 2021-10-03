Release type: minor

This release adds support for FastAPI integration using APIRouter.

```python
from fastapi import FastAPI
from strawberry.fastapi import GraphQL

from api.schema import schema

graphql_app = GraphQL(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

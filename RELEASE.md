Release type: minor

This release adds support for using FastAPI APIRouter arguments in GraphQLRouter.

Now you have the opportunity to specify parameters such as `tags`, `route_class`,
`deprecated`, `include_in_schema`, etc:

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

graphql_app = GraphQLRouter(schema, tags=["graphql"])

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

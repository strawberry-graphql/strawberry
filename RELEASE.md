Release type: minor

This release adds support for [starlite](https://starliteproject.dev/).

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
    def hello(self, info: Info[object, None]) -> str:
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

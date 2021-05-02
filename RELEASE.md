Release type: minor

This release adds an [aiohttp](https://github.com/aio-libs/aiohttp) integration for
Strawberry. The integration provides a `GraphQLView` class which can be used to
integrate Strawberry with aiohttp:

```python
import strawberry
from aiohttp import web
from strawberry.aiohttp.views import GraphQLView


@strawberry.type
class Query:
    pass


schema = strawberry.Schema(query=Query)

app = web.Application()

app.router.add_route("*", "/graphql", GraphQLView(schema=schema))
```

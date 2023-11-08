Release type: minor

This release adds support in _all_ all our HTTP integration for choosing between
different GraphQL IDEs. For now we support [GraphiQL](https://github.com/graphql/graphiql) (the default),
[Apollo Sandbox](https://www.apollographql.com/docs/graphos/explorer/sandbox/), and [Pathfinder](https://pathfinder.dev/).

**Deprecations:** This release deprecates the `graphiql` option in all HTTP integrations,
in favour of `graphql_ide`, this allows us to only have one settings to change GraphQL ide,
or to disable it.

Here's a couple of examples of how you can use this:

### FastAPI

```python
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from api.schema import schema

graphql_app = GraphQLRouter(schema, graphql_ide="apollo-sandbox")

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

### Django

```python
from django.urls import path

from strawberry.django.views import GraphQLView

from api.schema import schema

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema, graphql_ide="pathfinder")),
]
```

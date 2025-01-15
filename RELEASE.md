Release type: minor

## Add GraphQL Query batching support

GraphQL query batching is now supported across all frameworks (sync and async)
To enable query batching, set the `batch` parameter to True at the view level.

This makes your GraphQL API compatible with batching features supported by various
client side libraries, such as [Apollo GraphQL](https://www.apollographql.com/docs/react/api/link/apollo-link-batch-http) and [Relay](https://github.com/relay-tools/react-relay-network-modern?tab=readme-ov-file#batching-several-requests-into-one).

Example (FastAPI):

```py
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(schema, batch=True)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql/batch")
```

Example (Flask):
```py
from flask import Flask
from strawberry.flask.views import GraphQLView

from api.schema import schema

app = Flask(__name__)

app.add_url_rule(
    "/graphql/batch",
    view_func=GraphQLView.as_view("graphql_view", schema=schema, batch=True),
)

if __name__ == "__main__":
    app.run()
```

Note: Query Batching is not supported for multipart subscriptions

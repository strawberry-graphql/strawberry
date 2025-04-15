Release type: minor

## Add GraphQL Query batching support

GraphQL query batching is now supported across all frameworks (sync and async)
To enable query batching, set `batching_config.enabled` to True in the schema configuration.

This makes your GraphQL API compatible with batching features supported by various
client side libraries, such as [Apollo GraphQL](https://www.apollographql.com/docs/react/api/link/apollo-link-batch-http) and [Relay](https://github.com/relay-tools/react-relay-network-modern?tab=readme-ov-file#batching-several-requests-into-one).

Example (FastAPI):

```py
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(
    Query, config=StrawberryConfig(batching_config={"enabled": True})
)

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

Example (Flask):
```py
import strawberry

from flask import Flask
from strawberry.flask.views import GraphQLView

app = Flask(__name__)


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(
    Query, config=StrawberryConfig(batching_config={"enabled": True})
)

app.add_url_rule(
    "/graphql/batch",
    view_func=GraphQLView.as_view("graphql_view", schema=schema),
)

if __name__ == "__main__":
    app.run()
```

Note: Query Batching is not supported for multipart subscriptions

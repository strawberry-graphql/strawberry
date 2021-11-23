---
title: Chalice
---

# Chalice

Strawberry comes with an AWS Chalice integration. It provides a view that you can
use to serve your GraphQL schema:

Use the Chalice CLI to create a new project

```shell
chalice new-project badger-project
cd badger-project
```

Replace the contents of app.py with the following:

```python
from chalice import Chalice
from chalice.app import Request, Response

import strawberry
from strawberry.chalice.views import GraphQLView

app = Chalice(app_name="BadgerProject")


@strawberry.type
class Query:
    @strawberry.field
    def greetings(self) -> str:
        return "hello from the illustrious stack badger"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def echo(self, string_to_echo: str) -> str:
        return string_to_echo


schema = strawberry.Schema(query=Query, mutation=Mutation)
view = GraphQLView(schema=schema, render_graphiql=True)


@app.route("/graphql", methods=["GET", "POST"], content_types=["application/json"])
def handle_graphql() -> Response:
    request: Request = app.current_request
    result = view.execute_request(request)
    return result

```

And then run `chalice local` to start the localhost

```shell
chalice local
```

The GraphiQL interface can then be opened in your browser on http://localhost:8000/graphql

## Options

The `GraphQLView` accepts two options at the moment:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL interface.

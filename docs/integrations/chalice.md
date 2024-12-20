---
title: Chalice
---

# Chalice

Strawberry comes with an AWS Chalice integration. It provides a view that you
can use to serve your GraphQL schema:

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
view = GraphQLView(schema=schema)


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

The GraphiQL interface can then be opened in your browser on
http://localhost:8000/graphql

## Options

The `GraphQLView` accepts two options at the moment:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL
  interface.

## Extending the view

The base `GraphQLView` class can be extended by overriding any of the following
methods:

- `def get_context(self, request: Request, response: TemporalResponse) -> Context`
- `def get_root_value(self, request: Request) -> Optional[RootValue]`
- `def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def decode_json(self, data: Union[str, bytes]) -> object`
- `def encode_json(self, data: object) -> str`
- `def render_graphql_ide(self, request: Request) -> Response`

### get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request. By default; the `Response` object from `flask` is injected via the
parameters.

```python
import strawberry
from strawberry.chalice.views import GraphQLView
from strawberry.http.temporal import TemporalResponse
from chalice.app import Request


class MyGraphQLView(GraphQLView):
    def get_context(self, request: Request, response: TemporalResponse):
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        return str(info.context["example"])
```

Here we are returning a custom context dictionary that contains only one item
called "example".

Then we use the context in a resolver, the resolver will return "1" in this
case.

### get_root_value

`get_root_value` allows to provide a custom root value for your schema, this is
probably not used a lot but it might be useful in certain situations.

Here's an example:

```python
import strawberry
from strawberry.chalice.views import GraphQLView


class MyGraphQLView(GraphQLView):
    def get_root_value(self):
        return Query(name="Patrick")


@strawberry.type
class Query:
    name: str
```

Here we are returning a Query where the name is "Patrick", so we when requesting
the field name we'll return "Patrick" in this case.

### process_result

`process_result` allows to customize and/or process results before they are sent
to the clients. This can be useful logging errors or hiding them (for example to
hide internal exceptions).

It needs to return an object of `GraphQLHTTPResponse` and accepts the execution
result.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from strawberry.chalice.views import GraphQLView


class MyGraphQLView(GraphQLView):
    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [err.formatted for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

### decode_json

`decode_json` allows to customize the decoding of HTTP JSON requests. By default
we use `json.loads` but you can override this method to use a different decoder.

```python
from strawberry.chalice.views import GraphQLView
from typing import Union
import orjson


class MyGraphQLView(GraphQLView):
    def decode_json(self, data: Union[str, bytes]) -> object:
        return orjson.loads(data)
```

Make sure your code raises `json.JSONDecodeError` or a subclass of it if the
JSON cannot be decoded. The library shown in the example above, `orjson`, does
this by default.

### encode_json

`encode_json` allows to customize the encoding of HTTP and WebSocket JSON
responses. By default we use `json.dumps` but you can override this method to
use a different encoder.

```python
import json
from strawberry.chalice.views import GraphQLView


class MyGraphQLView(GraphQLView):
    def encode_json(self, data: object) -> str:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
from strawberry.chalice.views import GraphQLView
from chalice.app import Request, Response


class MyGraphQLView(GraphQLView):
    def render_graphql_ide(self, request: Request) -> Response:
        custom_html = """<html><body><h1>Custom GraphQL IDE</h1></body></html>"""

        return Response(custom_html, headers={"Content-Type": "text/html"})
```

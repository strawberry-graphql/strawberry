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

We allow to extend the base `GraphQLView`, by overriding the following methods:

- `get_context(self, request: Request, response: TemporalResponse) -> Any`
- `get_root_value(self, request: Request) -> Any`
- `process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `encode_json(self, response_data: GraphQLHTTPResponse) -> str`

## get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request. By default; the `Response` object from `flask` is injected via the
parameters.

```python
class MyGraphQLView(GraphQLView):
    def get_context(self, response: Response) -> Any:
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

## get_root_value

`get_root_value` allows to provide a custom root value for your schema, this is
probably not used a lot but it might be useful in certain situations.

Here's an example:

```python
class MyGraphQLView(GraphQLView):
    def get_root_value(self) -> Any:
        return Query(name="Patrick")


@strawberry.type
class Query:
    name: str
```

Here we are returning a Query where the name is "Patrick", so we when requesting
the field name we'll return "Patrick" in this case.

## process_result

`process_result` allows to customize and/or process results before they are sent
to the clients. This can be useful logging errors or hiding them (for example to
hide internal exceptions).

It needs to return an object of `GraphQLHTTPResponse` and accepts the execution
result.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult


class MyGraphQLView(GraphQLView):
    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [err.formatted for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

## encode_json

`encode_json` allows to customize the encoding of the JSON response. By default
we use `json.dumps` but you can override this method to use a different encoder.

```python
class MyGraphQLView(GraphQLView):
    def encode_json(self, data: GraphQLHTTPResponse) -> str:
        return json.dumps(data, indent=2)
```

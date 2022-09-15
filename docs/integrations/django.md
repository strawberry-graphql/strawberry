---
title: Django
---

# Django

Strawberry comes with a basic
[Django integration](https://github.com/strawberry-graphql/strawberry-graphql-django).
It provides a view that you can use to serve your GraphQL schema:

```python
from django.urls import path

from strawberry.django.views import GraphQLView

from api.schema import schema

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema)),
]
```

You'd also need to add `strawberry.django` to the `INSTALLED_APPS` of your
project, this is needed to provide the template for the GraphiQL interface.

## Options

The `GraphQLView` accepts the following arguments:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL
  interface.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests
- `subscriptions_enabled`: optional boolean paramenter enabling subscriptions in
  the GraphiQL interface, defaults to `False`.
- `json_encoder`: optional JSON encoder, defaults to `DjangoJSONEncoder`, will
  be used to serialize the data.
- `json_dumps_params`: optional dictionary of keyword arguments to pass to the
  `json.dumps` call used to generate the response. To get the most compact JSON
  representation, you should specify `{"separators": (",", ":")}`, defaults to
  `None`.

## Extending the view

We allow to extend the base `GraphQLView`, by overriding the following methods:

- `get_context(self, request: HttpRequest) -> Any`
- `get_root_value(self, request: HttpRequest) -> Any`
- `process_result(self, request: HttpRequest, result: ExecutionResult) -> GraphQLHTTPResponse`

## get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a
`StrawberryDjangoContext` object.

```python
@strawberry.type
class Query:
    @strawberry.field
    def user(self, info: Info) -> str:
        return str(info.context.request.user)
```

or in case of a custom context:

```python
class MyGraphQLView(GraphQLView):
    def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: Info) -> str:
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
    def get_root_value(self, request: HttpRequest) -> Any:
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

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and the execution results.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from graphql.error.graphql_error import format_error as format_graphql_error

class MyGraphQLView(GraphQLView):
    def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [format_graphql_error(err) for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

# Async Django

Strawberry also provides an async view that you can use with Django 3.1+

```python
from django.urls import path

from strawberry.django.views import AsyncGraphQLView

from api.schema import schema

urlpatterns = [
    path("graphql/", AsyncGraphQLView.as_view(schema=schema)),
]
```

You'd also need to add `strawberry.django` to the `INSTALLED_APPS` of your
project, this is needed to provide the template for the GraphiQL interface.

## Options

The `AsyncGraphQLView` accepts the following arguments:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphiql`: optional, defaults to `True`, whether to enable the GraphiQL
  interface.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests
- `subscriptions_enabled`: optional boolean paramenter enabling subscriptions in
  the GraphiQL interface, defaults to `False`.
- `json_encoder`: optional JSON encoder, defaults to `DjangoJSONEncoder`, will
  be used to serialize the data.
- `json_dumps_params`: optional dictionary of keyword arguments to pass to the
  `json.dumps` call used to generate the response. To get the most compact JSON
  representation, you should specify `{"separators": (",", ":")}`, defaults to
  `None`.

## Extending the view

We allow to extend the base `AsyncGraphQLView`, by overriding the following
methods:

- `async get_context(self, request: HttpRequest) -> Any`
- `async get_root_value(self, request: HttpRequest) -> Any`
- `async process_result(self, request: HttpRequest, result: ExecutionResult) -> GraphQLHTTPResponse`

## get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request.

```python
class MyGraphQLView(AsyncGraphQLView):
    async def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: Info) -> str:
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
class MyGraphQLView(AsyncGraphQLView):
    async def get_root_value(self, request: HttpRequest) -> Any:
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

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and the execution results.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from graphql.error.graphql_error import format_error as format_graphql_error

class MyGraphQLView(AsyncGraphQLView):
    async def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [format_graphql_error(err) for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

## Subscriptions

Subscriptions run over websockets and thus depend on
[channels](https://channels.readthedocs.io/). Take a look at our
[channels integraton](/docs/integrations/channels.md) page for more information regarding it.

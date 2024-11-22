---
title: Django
---

# Django

Strawberry comes with a basic
[Django integration](https://github.com/strawberry-graphql/strawberry-graphql-django).
It provides a view that you can use to serve your GraphQL schema:

```python
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from strawberry.django.views import GraphQLView

from api.schema import schema

urlpatterns = [
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema))),
]
```

Strawberry only provides a GraphQL view for Django,
[Strawberry GraphQL Django](https://github.com/strawberry-graphql/strawberry-graphql-django)
provides integration with the models. `import strawberry_django` should do the
same as `import strawberry.django` if both libraries are installed.

You'd also need to add `strawberry_django` to the `INSTALLED_APPS` of your
project, this is needed to provide the template for the GraphiQL interface.

## Options

The `GraphQLView` accepts the following arguments:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphql_ide`: optional, defaults to `"graphiql"`, allows to choose the
  GraphQL IDE interface (one of `graphiql`, `apollo-sandbox` or `pathfinder`) or
  to disable it by passing `None`.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests
- `multipart_uploads_enabled`: optional, defaults to `False`, controls whether
  to enable multipart uploads. Please make sure to consider the
  [security implications mentioned in the GraphQL Multipart Request Specification](https://github.com/jaydenseric/graphql-multipart-request-spec/blob/master/readme.md#security)
  when enabling this feature.

## Deprecated options

The following options are deprecated and will be removed in a future release:

- `json_encoder`: optional JSON encoder, defaults to `DjangoJSONEncoder`, will
  be used to serialize the data.
- `json_dumps_params`: optional dictionary of keyword arguments to pass to the
  `json.dumps` call used to generate the response. To get the most compact JSON
  representation, you should specify `{"separators": (",", ":")}`, defaults to
  `None`.

You can extend the view and override `encode_json` to customize the JSON
encoding process.

## Extending the view

We allow to extend the base `GraphQLView`, by overriding the following methods:

- `def get_context(self, request: HttpRequest, response: HttpResponse) -> Context`
- `def get_root_value(self, request: HttpRequest) -> Optional[RootValue]`
- `def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def decode_json(self, data: Union[str, bytes]) -> object`
- `def encode_json(self, data: object) -> str`
- `def render_graphql_ide(self, request: HttpRequest) -> HttpResponse`

### get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a
`StrawberryDjangoContext` object.

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def user(self, info: strawberry.Info) -> str:
        return str(info.context.request.user)
```

or in case of a custom context:

```python
import strawberry
from strawberry.django.views import GraphQLView
from django.http import HttpRequest, HttpResponse


class MyGraphQLView(GraphQLView):
    def get_context(self, request: HttpRequest, response: HttpResponse):
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
from strawberry.django.views import GraphQLView
from django.http import HttpRequest


class MyGraphQLView(GraphQLView):
    def get_root_value(self, request: HttpRequest):
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

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and the execution results.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from strawberry.django.views import GraphQLView
from django.http import HttpRequest


class MyGraphQLView(GraphQLView):
    def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [err.formatted for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

### decode_json

`decode_json` allows to customize the decoding of HTTP and WebSocket JSON
requests. By default we use `json.loads` but you can override this method to use
a different decoder.

```python
from strawberry.django.views import GraphQLView
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
from strawberry.django.views import GraphQLView


class MyGraphQLView(GraphQLView):
    def encode_json(self, data: object) -> str:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
from strawberry.django.views import GraphQLView
from django.http import HttpResponse, HttpRequest
from django.template.loader import render_to_string


class MyGraphQLView(GraphQLView):
    def render_graphql_ide(self, request: HttpRequest) -> HttpResponse:
        content = render_to_string("myapp/my_graphql_ide_template.html")

        return HttpResponse(content)
```

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

You'd also need to add `strawberry_django` to the `INSTALLED_APPS` of your
project, this is needed to provide the template for the GraphiQL interface.

## Options

The `AsyncGraphQLView` accepts the following arguments:

- `schema`: mandatory, the schema created by `strawberry.Schema`.
- `graphql_ide`: optional, defaults to `"graphiql"`, allows to choose the
  GraphQL IDE interface (one of `graphiql`, `apollo-sandbox` or `pathfinder`) or
  to disable it by passing `None`.
- `allow_queries_via_get`: optional, defaults to `True`, whether to enable
  queries via `GET` requests

## Extending the view

The base `AsyncGraphQLView` class can be extended by overriding any of the
following methods:

- `async def get_context(self, request: HttpRequest, response: HttpResponse) -> Context`
- `async def get_root_value(self, request: HttpRequest) -> Optional[RootValue]`
- `async def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse`
- `def decode_json(self, data: Union[str, bytes]) -> object`
- `def encode_json(self, data: object) -> str`
- `async def render_graphql_ide(self, request: HttpRequest) -> HttpResponse`

### get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request.

```python
import strawberry
from strawberry.django.views import AsyncGraphQLView
from django.http import HttpRequest, HttpResponse


class MyGraphQLView(AsyncGraphQLView):
    async def get_context(self, request: HttpRequest, response: HttpResponse):
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
from strawberry.django.views import AsyncGraphQLView
from django.http import HttpRequest


class MyGraphQLView(AsyncGraphQLView):
    async def get_root_value(self, request: HttpRequest):
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

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and the execution results.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from strawberry.django.views import AsyncGraphQLView
from django.http import HttpRequest


class MyGraphQLView(AsyncGraphQLView):
    async def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [err.formatted for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

### decode_json

`decode_json` allows to customize the decoding of HTTP and WebSocket JSON
requests. By default we use `json.loads` but you can override this method to use
a different decoder.

```python
from strawberry.django.views import AsyncGraphQLView
from typing import Union
import orjson


class MyGraphQLView(AsyncGraphQLView):
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
from strawberry.django.views import AsyncGraphQLView


class MyGraphQLView(AsyncGraphQLView):
    def encode_json(self, data: object) -> str:
        return json.dumps(data, indent=2)
```

### render_graphql_ide

In case you need more control over the rendering of the GraphQL IDE than the
`graphql_ide` option provides, you can override the `render_graphql_ide` method.

```python
from strawberry.django.views import AsyncGraphQLView
from django.http import HttpResponse
from django.template.loader import render_to_string


class MyGraphQLView(AsyncGraphQLView):
    async def render_graphql_ide(self, request: HttpRequest) -> HttpResponse:
        content = render_to_string("myapp/my_graphql_ide_template.html")

        return HttpResponse(content)
```

## Subscriptions

Subscriptions run over websockets and thus depend on
[channels](https://channels.readthedocs.io/). Take a look at our
[channels integraton](./channels.md) page for more information regarding it.

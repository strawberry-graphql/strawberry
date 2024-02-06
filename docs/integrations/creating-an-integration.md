---
title: Adding an integration
---

# Adding an integration

Strawberry provides a set of integrations with other libraries, such as Django,
FastAPI, Flask, and more, but you can also add your own integration. This guide
will show you how to do that.

## Base views

Strawberry includes two base views that you can use to create your own
integrations:

- `SyncBaseHTTPView`: a base view for synchronous integrations
- `AsyncBaseHTTPView`: a base view for asynchronous integrations

Both views are provides the same API, with the main difference being that the
`AsyncBaseHTTPView`'s methods are async.

## Creating a view

To create a view, you need to create a class that inherits from either
`SyncBaseHTTPView` or `AsyncBaseHTTPView` and implement the `get_root_value`
method. Here is an example of a view that inherits from `AsyncBaseHTTPView`:

```python
from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.temporal_response import TemporalResponse
from strawberry.http.typevars import Context, RootValue


class MyView(
    AsyncBaseHTTPView[
        MyRequest,
        MyResponse,
        TemporalResponse,
        Context,
        RootValue,
    ]
):
    @property
    def allow_queries_via_get(self) -> bool:
        # this will usually be a setting on the view
        return True

    async def get_sub_response(self, request: MyRequest) -> TemporalResponse:
        return TemporalResponse(status_code=200)

    async def get_context(self, request: Request, response: SubResponse) -> Context:
        return {"request": request, "response": response}

    async def get_root_value(self, request: Request) -> Optional[RootValue]:
        return None

    def render_graphql_ide(self, request: Request) -> Response: ...

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: SubResponse
    ) -> Response: ...
```

The methods above are the bare minimum that you need to implement to create a
view. They are all required, but you can also override other methods to change
the behaviour of the view.

On top of that we also need a request adapter, here's the base class for the
async version:

```python
from strawberry.http.types import HTTPMethod, QueryParams, FormData


class AsyncHTTPRequestAdapter:
    @property
    def query_params(self) -> Mapping[str, Optional[Union[str, List[str]]]]: ...

    @property
    def method(self) -> HTTPMethod: ...

    @property
    def headers(self) -> Mapping[str, str]: ...

    @property
    def content_type(self) -> Optional[str]: ...

    async def get_body(self) -> Union[bytes, str]: ...

    async def get_form_data(self) -> FormData: ...
```

This request adapter will be used to get the request data from the request
object. You can specify the request adapter to use by setting the
`request_adapter_class` attribute on the view.

```python
class MyView(
    AsyncBaseHTTPView[
        MyRequest,
        MyResponse,
        TemporalResponse,
        Context,
        RootValue,
    ]
):
    request_adapter_class = MyRequestAdapter
```

Finally you need to execute the operation, the base view provides a `run` method
that you can use to do that:

```python
from strawberry.http.exceptions import HTTPException


class MyView(
    AsyncBaseHTTPView[
        MyRequest,
        MyResponse,
        TemporalResponse,
        Context,
        RootValue,
    ]
):
    ...

    async def get(self, request: MyRequest) -> MyResponse:
        try:
            return await self.run(request)
        except HTTPException as e:
            response = Response(e.reason, status_code=e.status_code)
```

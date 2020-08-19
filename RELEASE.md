Release type: patch

Add `process_result` to views for Django, Flask and ASGI. They can be overriden
to provide a custom response and also to process results and errors.

It also removes `request` from Flask view's `get_root_value` and `get_context`
since request in Flask is a global.

Django example:

```python
# views.py
from django.http import HttpRequest
from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.schema import ExecutionResult

class GraphQLView(BaseGraphQLView):
    def process_result(self, request: HttpRequest, result: ExecutionResult) -> GraphQLHTTPResponse:
        return {"data": result.data, "errors": result.errors or []}

```

Flask example:

```python
# views.py
from strawberry.flask.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.schema import ExecutionResult

class GraphQLView(BaseGraphQLView):
    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return {"data": result.data, "errors": result.errors or []}

```

ASGI example:

```python
from strawberry.asgi import GraphQL as BaseGraphQL
from strawberry.http import GraphQLHTTPResponse
from strawberry.schema import ExecutionResult
from starlette.requests import Request

from .schema import schema

class GraphQL(BaseGraphQLView):
    async def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse:
        return {"data": result.data, "errors": result.errors or []}

```

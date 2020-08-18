Release type: patch

Add `process_result` to views for Django, Flask and ASGI. They can be overriden
to provide a custom response and also to process results and errors.

Django example:

```python
# views.py
from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.schema import ExecutionResult

class GraphQLView(BaseGraphQLView):
    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
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

from .schema import schema

class GraphQL(BaseGraphQLView):
    async def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return {"data": result.data, "errors": result.errors or []}

```

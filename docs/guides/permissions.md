---
title: Permissions
---

# Permissions

Permissions can be managed using `Permission` classes. A `Permission` class extends `BasePermission` and has a `has_permission` method. It can be hooked up to a field using the `permission_classes` keyword argument. A simple example looks like this:

```python
import strawberry
from strawberry.permission import BasePermission
from strawberry.types import Info

class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        return False

@strawberry.type
class Query:
    user: str = strawberry.field(permission_classes=[IsAuthenticated])
```

If the `has_permission` method fails then an error will be raised using the `message` class attribute. See [Dealing with Errors](/docs/guides/errors) for more information.

```json
{
  "data": null,
  "errors": [
    {
      "message": "User is not authenticated"
    }
  ]
}
```

In a simple use case you could obtain all the information you need to execute the `has_permission` check from the `source` and `info` objects.

For more complex cases it might need more information from the Request. This can be provided by extending the `GraphQL` class to provide more context. The `Permission` class can then use that context from the `Info` object.

```python
from strawberry.asgi import GraphQL

from starlette.requests import Request
from starlette.websockets import WebSocket


class MyGraphQL(GraphQL):
    async def get_context(self, request: typing.Union[Request, WebSocket]) -> Any:
        return {
            "auth": request.headers["Authorization"] or request.query_params["auth"]
        }
```

In this example the `MyGraphQL` class extends the Strawberry `GraphQL` class to provide a `get_context` helper. This helper is used to fill the `Info` object. You should be aware that `Request` and `WebSocket` objects have different attributes and methods, and you may need to handle retrieving authorization details from them differently.

*For more information on using context see the [Data Loaders](/docs/guides/dataloaders) docs.*

The `Info` object can then be accessed in a `Permission` class like:

```python
from myauth import authenticate

class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        return authenticate(info.context["auth"])
```

Here we are taking the `auth` key out of the `info.context` dictionary and passing it to an `authenticate` method we have implemented somewhere else in our codebase.

Beyond providing hooks, Authentication is not currently Strawberry's responsibility. You should provide your own helpers to figure out if a request has the permissions you expect.

*For more discussion on Authentication see [Issue #830](https://github.com/strawberry-graphql/strawberry/issues/830).*

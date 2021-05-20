---
title: Permissions
---

# Permissions

Permissions can be managed using `Permission` classes. A `Permission` class extends `BasePermission` and has a `has_permission` method. It can be added to a field using the `permission_classes` keyword argument. A simple example looks like this:

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

If the `has_permission` method fails then an error will be raised using the `message` class attribute. See [Dealing with Errors](/docs/guides/errors) for more information on how errors are handled.

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

In most use cases you can obtain all the information you need to execute the `has_permission` check from the `source` and `info` objects. For example the `info` object contains a `context` dictionary, which includes the Request object. The Request object can be used to retrieve headers, query parameters, or cookies that can be used for auth like so:

```python
from myauth import authenticate_header, authenticate_query_param

from starlette.requests import Request
from starlette.websockets import WebSocket

class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        request: Union[Request, Websocket] = info.context["request"]
        if "Authorization" in request.headers:
            return authenticate_header(request)
        if "auth" in request.query_params:
            return authenticate_query_params(request)
        return False
```

Here we retrieve the `request` object from the `context` provided by `info`. This object will be either a `Request` or `Websocket` instance from `starlette` (see: [Request docs](https://www.starlette.io/requests/) and [Websocket docs](https://www.starlette.io/websockets/)).

In the next step we take either the `Authorization` header or the `auth` query parameter out of the `request` object, depending on which is available. We then pass those on to some authenticate methods we've implemented ourselves.

Beyond providing hooks, Authentication is not currently Strawberry's responsibility. You should provide your own helpers to figure out if a request has the permissions you expect.

*For more discussion on Authentication see [Issue #830](https://github.com/strawberry-graphql/strawberry/issues/830).*

---
title: Permissions
---

# Permissions

Permissions can be managed using `Permission` classes. A `Permission` class
extends `BasePermission` and has a `has_permission` method. It can be added to a
field using the `permission_classes` keyword argument. A basic example looks
like this:

```python
import typing
import strawberry
from strawberry.permission import BasePermission
from strawberry.types import Info

class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    # This method can also be async!
    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        return False

@strawberry.type
class Query:
    user: str = strawberry.field(permission_classes=[IsAuthenticated])
```

Your `has_permission` method should check if this request has permission to access the
field. Note that the `has_permission` method can also be asynchronous.

If the `has_permission` method returns a truthy value then the field access will go
ahead. Otherwise, an error will be raised using the `message` class attribute.

Take a look at our [Dealing with Errors Guide](/docs/guides/errors) for more information
on how errors are handled.

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

## Accessing user information

Accessing the current user information to implement your permission checks
depends on the web framework you are using.

Most frameworks will have a `Request` object where you can either access the current
user directly or access headers/cookies/query parameters to authenticate the user.

All the Strawberry integrations provide this Request object in the `info.context` object
that is accessible in every resolver and in the `has_permission` function.

You can find more details about a specific framework integration under the
"Integrations" heading in the navigation.

In this example we are using `starlette` which uses the
[ASGI](/docs/integrations/asgi) integration:

```python
import typing
from myauth import authenticate_header, authenticate_query_param

from starlette.requests import Request
from starlette.websockets import WebSocket
from strawberry.permission import BasePermission
from strawberry.types import Info

class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        request: typing.Union[Request, WebSocket] = info.context["request"]

        if "Authorization" in request.headers:
            return authenticate_header(request)

        if "auth" in request.query_params:
            return authenticate_query_params(request)

        return False
```

Here we retrieve the `request` object from the `context` provided by `info`.
This object will be either a `Request` or `Websocket` instance from `starlette`
(see: [Request docs](https://www.starlette.io/requests/) and
[Websocket docs](https://www.starlette.io/websockets/)).

In the next step we take either the `Authorization` header or the `auth` query
parameter out of the `request` object, depending on which is available. We then
pass those on to some authenticate methods we've implemented ourselves.

Beyond providing hooks, Authentication is not currently Strawberry's
responsibility. You should provide your own helpers to figure out if a request
has the permissions you expect.

_For more discussion on Authentication see_
_[Issue #830](https://github.com/strawberry-graphql/strawberry/issues/830)._

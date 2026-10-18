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


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    # This method can also be async!
    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs
    ) -> bool:
        return False


@strawberry.type
class Query:
    user: str = strawberry.field(permission_classes=[IsAuthenticated])
```

Your `has_permission` method should check if this request has permission to
access the field. Note that the `has_permission` method can also be
asynchronous.

If the `has_permission` method returns a truthy value then the field access will
go ahead. Otherwise, an error will be raised using the `message` class
attribute.

Take a look at our [Dealing with Errors Guide](/docs/guides/errors) for more
information on how errors are handled.

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

Most frameworks will have a `Request` object where you can either access the
current user directly or access headers/cookies/query parameters to authenticate
the user.

All the Strawberry integrations provide this Request object in the
`info.context` object that is accessible in every resolver and in the
`has_permission` function.

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


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs
    ) -> bool:
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

## Custom Error Extensions & classes

In addition to the message, permissions automatically add pre-defined error
extensions to the error, and can use a custom `GraphQLError` class. This can be
configured by modifying the `error_class` and `error_extensions` attributes on
the `BasePermission` class. Error extensions will be propagated to the response
as specified in the
[GraphQL spec](https://strawberry.rocks/docs/types/exceptions).

```python
import typing

from strawberry.permission import BasePermission

from your_business_logic import GQLNotImplementedError


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"
    error_class = GQLNotImplementedError
    error_extensions = {"code": "UNAUTHORIZED"}

    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs
    ) -> bool:
        return False
```

# Advanced Permissions

Internally, permissions in strawberry use the `PermissionsExtension` field
extension.

The following snippet

```python
import strawberry


@strawberry.type
class Query:
    user: str = strawberry.field(permission_classes=[IsAuthenticated])
```

is internally equivalent to

```python
import strawberry
from strawberry.permission import PermissionExtension


@strawberry.type
class Query:
    @strawberry.field(extensions=[PermissionExtension(permissions=[IsAuthenticated()])])
    def name(self) -> str:
        return "ABC"
```

Using the new `PermissionExtension` API, permissions support even more features:

## Silent errors

In some cases, it is practical to avoid throwing an error when the user has no
permission to access the field and instead return `None` or an empty list to the
client. To return `None` or `[]` instead of raising an error, the
`fail_silently ` keyword argument on `PermissionExtension` can be set to `True`:

<Warning>
  Note that this will only work if the field returns a type that is nullable or
  a list, e.g. `Optional[str]` or `List[str]`.
</Warning>

```python
import strawberry
from strawberry.permission import PermissionExtension, BasePermission
from typing import Optional


@strawberry.type
class Query:
    @strawberry.field(
        extensions=[
            PermissionExtension(permissions=[IsAuthenticated()], fail_silently=True)
        ]
    )
    def name(self) -> Optional[str]:
        return "ABC"
```

Please note than in many cases, defensive programming is a better approach than
using `fail_silently`. Clients will no longer be able to distinguish between a
permission error and an empty result. Before implementing `fail_silently`,
consider if it is possible to use alternative solutions like the `@skip` or
`@include` directives to dynamically exclude fields from the query for users
without permission. Check the GraphQL documentation for more information on
[directives](https://graphql.org/learn/queries/#directives).

## Customizable Error Handling

To customize the error handling, the `on_unauthorized` method on the
`BasePermission` class can be used. Further changes can be implemented by
subclassing the `PermissionExtension` class.

## Combining permissions with the `|` operator

Permission instances can be combined with the `|` operator. Access is granted if
_any_ of the combined permissions grants it, which is useful when a field can be
reached by more than one kind of user:

```python
import strawberry
from strawberry.permission import PermissionExtension


@strawberry.type
class User:
    @strawberry.field(
        extensions=[
            PermissionExtension(
                # require auth AND (user is the owner OR user is staff)
                permissions=[IsAuthenticated(), IsOwner() | IsStaff()]
            )
        ]
    )
    def ssn(self) -> str:
        return "555-55-5555"
```

The combined permissions are evaluated from left to right and evaluation stops
at the first permission that grants access. Sync and async permissions can be
mixed freely. A combination made only of sync permissions always evaluates them
synchronously, even when the field's other permissions or resolver are async, so
a permission that returns an awaitable must be declared with `async def`.

Chaining is supported: `A() | B() | C()`, `(A() | B()) | C()` and
`A() | (B() | C())` are equivalent and all produce a single combined permission.

When none of the permissions grants access, the error of the **first**
permission is raised, including its `message`, `error_class`, `error_extensions`
and custom `on_unauthorized` behavior. To give the combination its own name and
error, subclass `OrPermission` and set `message` (or override `on_unauthorized`)
like you would for any other permission:

```python
from strawberry.permission import OrPermission


class IsOwnerOrStaff(OrPermission):
    message = "Only the owner or staff can see this"


permission = IsOwnerOrStaff(IsOwner(), IsStaff())
```

A subclass may also override `has_permission`. The combination then uses your
override as-is, so you are responsible for awaiting async permissions yourself.
Pick a name that does not clash with a derived one: `AdminOrOwner` would collide
with `Admin() | Owner()`, and schema construction reports a directive collision.

A combined permission adds a single schema directive to the schema. Its name is
built from the permission class names, sorted alphabetically and joined with
`Or`, for example `@isOwnerOrIsStaff`. The same directive is reused on every
field, regardless of the order of the operands. The directive has no arguments,
so combining two instances of the same class, like
`HasRole("admin") | HasRole("editor")`, is printed as `@hasRoleOrHasRole`.
Because chained combinations are flattened, a custom `_schema_directive` set on
an intermediate combination is not kept; set it on the final combination or use
a subclass.

<Note>
  The `|` operator combines permission _instances_, so use it with
  `PermissionExtension`. Writing `IsOwner | IsStaff` on the classes themselves
  creates a regular Python type union, not a permission, and fails when the
  schema is built; the `permission_classes` argument takes classes and can't be
  combined this way.
</Note>

## Schema Directives

Permissions will automatically be added as schema directives to the schema. This
behavior can be altered by setting the `use_directives` to `False` on
`PermissionExtension`, or by setting the `_schema_directive` class attribute of
the permission class to a custom directive.

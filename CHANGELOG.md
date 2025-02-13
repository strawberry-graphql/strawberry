CHANGELOG
=========

0.260.2 - 2025-02-13
--------------------

This release fixes an issue where directives with input types using snake_case
would not be printed in the schema.

For example, the following:

```python
@strawberry.input
class FooInput:
    hello: str
    hello_world: str


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class FooDirective:
    input: FooInput


@strawberry.type
class Query:
    @strawberry.field(
        directives=[
            FooDirective(input=FooInput(hello="hello", hello_world="hello world")),
        ]
    )
    def foo(self, info) -> str: ...
```

Would previously print as:

```graphql
directive @fooDirective(
  input: FooInput!
  optionalInput: FooInput
) on FIELD_DEFINITION

type Query {
  foo: String! @fooDirective(input: { hello: "hello" })
}

input FooInput {
  hello: String!
  hello_world: String!
}
```

Now it will be correctly printed as:

```graphql
directive @fooDirective(
  input: FooInput!
  optionalInput: FooInput
) on FIELD_DEFINITION

type Query {
  foo: String!
    @fooDirective(input: { hello: "hello", helloWorld: "hello world" })
}

input FooInput {
  hello: String!
  hello_world: String!
}
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3780](https://github.com/strawberry-graphql/strawberry/pull/3780/)


0.260.1 - 2025-02-13
--------------------

This release fixes an issue where extensions were being duplicated when custom directives were added to the schema. Previously, when user directives were present, extensions were being appended twice to the extension list, causing them to be executed multiple times during query processing.

The fix ensures that extensions are added only once and maintains their original order. Test cases have been added to validate this behavior and ensure extensions are executed exactly once.

Contributed by [DONEY K PAUL](https://github.com/doney-dkp) via [PR #3783](https://github.com/strawberry-graphql/strawberry/pull/3783/)


0.260.0 - 2025-02-12
--------------------

Support aliases (TypeVar passthrough) in `get_specialized_type_var_map`.

Contributed by [Alexey Pelykh](https://github.com/alexey-pelykh) via [PR #3766](https://github.com/strawberry-graphql/strawberry/pull/3766/)


0.259.1 - 2025-02-12
--------------------

This release adjusts the `context_getter` attribute from the fastapi `GraphQLRouter`
to accept an async callables.

Contributed by [Alexey Pelykh](https://github.com/alexey-pelykh) via [PR #3763](https://github.com/strawberry-graphql/strawberry/pull/3763/)


0.259.0 - 2025-02-09
--------------------

This release refactors some of the internal execution logic by:

1. Moving execution logic from separate files into schema.py for better organization
2. Using graphql-core's parse and validate functions directly instead of wrapping them
3. Removing redundant execute.py and subscribe.py files

This is an internal refactor that should not affect the public API or functionality. The changes make the codebase simpler and easier to maintain.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3771](https://github.com/strawberry-graphql/strawberry/pull/3771/)


0.258.1 - 2025-02-09
--------------------

This release adjusts the schema printer to avoid printing a schema directive
value set to `UNSET` as `""` (empty string).

For example, the following:

```python
@strawberry.input
class FooInput:
    a: str | None = strawberry.UNSET
    b: str | None = strawberry.UNSET


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class FooDirective:
    input: FooInput


@strawberry.type
class Query:
    @strawberry.field(directives=[FooDirective(input=FooInput(a="aaa"))])
    def foo(self, info) -> str: ...
```

Would previously print as:

```graphql
directive @fooDirective(
  input: FooInput!
  optionalInput: FooInput
) on FIELD_DEFINITION

type Query {
  foo: String! @fooDirective(input: { a: "aaa", b: "" })
}

input FooInput {
  a: String
  b: String
}
```

Now it will be correctly printed as:

```graphql
directive @fooDirective(
  input: FooInput!
  optionalInput: FooInput
) on FIELD_DEFINITION

type Query {
  foo: String! @fooDirective(input: { a: "aaa" })
}

input FooInput {
  a: String
  b: String
}
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3770](https://github.com/strawberry-graphql/strawberry/pull/3770/)


0.258.0 - 2025-01-12
--------------------

Add the ability to override the "max results" a relay's connection can return on
a per-field basis.

The default value for this is defined in the schema's config, and set to `100`
unless modified by the user. Now, that per-field value will take precedence over
it.

For example:

```python
@strawerry.type
class Query:
    # This will still use the default value in the schema's config
    fruits: ListConnection[Fruit] = relay.connection()

    # This will reduce the maximum number of results to 10
    limited_fruits: ListConnection[Fruit] = relay.connection(max_results=10)

    # This will increase the maximum number of results to 10
    higher_limited_fruits: ListConnection[Fruit] = relay.connection(max_results=10_000)
```

Note that this only affects `ListConnection` and subclasses. If you are
implementing your own connection resolver, there's an extra keyword named
`max_results: int | None` that will be passed to it.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3746](https://github.com/strawberry-graphql/strawberry/pull/3746/)


0.257.0 - 2025-01-09
--------------------

The common `node: Node` used to resolve relay nodes means we will be relying on
is_type_of to check if the returned object is in fact a subclass of the Node
interface.

However, integrations such as Django, SQLAlchemy and Pydantic will not return
the type itself, but instead an alike object that is later resolved to the
expected type.

In case there are more than one possible type defined for that model that is
being returned, the first one that replies True to `is_type_of` check would be
used in the resolution, meaning that when asking for `"PublicUser:123"`,
strawberry could end up returning `"User:123"`, which can lead to security
issues (such as data leakage).

In here we are introducing a new `strawberry.cast`, which will be used to mark
an object with the already known type by us, and when asking for is_type_of that
mark will be used to check instead, ensuring we will return the correct type.

That `cast` is already in place for the relay node resolution and pydantic.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3749](https://github.com/strawberry-graphql/strawberry/pull/3749/)


0.256.1 - 2024-12-23
--------------------

This release updates Strawberry internally to no longer pass keywords arguments
to `pathlib.PurePath`. Support for supplying keyword arguments to
`pathlib.PurePath` is deprecated and scheduled for removal in Python 3.14

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3738](https://github.com/strawberry-graphql/strawberry/pull/3738/)


0.256.0 - 2024-12-21
--------------------

This release drops support for Python 3.8, which reached its end-of-life (EOL)
in October 2024. The minimum supported Python version is now 3.9.

We strongly recommend upgrading to Python 3.9 or a newer version, as older
versions are no longer maintained and may contain security vulnerabilities.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3730](https://github.com/strawberry-graphql/strawberry/pull/3730/)


0.255.0 - 2024-12-20
--------------------

This release adds support for making Relay connection optional, this is useful
when you want to add permission classes to the connection and not fail the whole
query if the user doesn't have permission to access the connection.

Example:

```python
import strawberry
from strawberry import relay
from strawberry.permission import BasePermission


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    # This method can also be async!
    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs
    ) -> bool:
        return False


@strawberry.type
class Fruit(relay.Node):
    code: relay.NodeID[int]
    name: str
    weight: float

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: strawberry.Info,
        node_ids: Iterable[str],
    ):
        return []


@strawberry.type
class Query:
    node: relay.Node = relay.node()

    @relay.connection(
        relay.ListConnection[Fruit] | None, permission_classes=[IsAuthenticated()]
    )
    def fruits(self) -> Iterable[Fruit]:
        # This can be a database query, a generator, an async generator, etc
        return all_fruits.values()
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3707](https://github.com/strawberry-graphql/strawberry/pull/3707/)


0.254.1 - 2024-12-20
--------------------

This release updates the Context and RootValue vars to have
a default value of `None`, this makes it easier to use the views
without having to pass in a value for these vars.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3732](https://github.com/strawberry-graphql/strawberry/pull/3732/)


0.254.0 - 2024-12-13
--------------------

This release adds a new `on_ws_connect` method to all HTTP view integrations.
The method is called when a `graphql-transport-ws` or `graphql-ws` connection is
established and can be used to customize the connection acknowledgment behavior.

This is particularly useful for authentication, authorization, and sending a
custom acknowledgment payload to clients when a connection is accepted. For
example:

```python
class MyGraphQLView(GraphQLView):
    async def on_ws_connect(self, context: Dict[str, object]):
        connection_params = context["connection_params"]

        if not isinstance(connection_params, dict):
            # Reject without a custom graphql-ws error payload
            raise ConnectionRejectionError()

        if connection_params.get("password") != "secret:
            # Reject with a custom graphql-ws error payload
            raise ConnectionRejectionError({"reason": "Invalid password"})

        if username := connection_params.get("username"):
            # Accept with a custom acknowledgement payload
            return {"message": f"Hello, {username}!"}

        # Accept without a acknowledgement payload
        return await super().on_ws_connect(context)
```

Take a look at our documentation to learn more.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3720](https://github.com/strawberry-graphql/strawberry/pull/3720/)


0.253.1 - 2024-12-03
--------------------

Description:
Fixed a bug in the OpenTelemetryExtension class where the _span_holder dictionary was incorrectly shared across all instances. This was caused by defining _span_holder as a class-level attribute with a mutable default value (dict()).

Contributed by [Conglei](https://github.com/conglei) via [PR #3716](https://github.com/strawberry-graphql/strawberry/pull/3716/)


0.253.0 - 2024-11-23
--------------------

In this release, the return types of the `get_root_value` and `get_context`
methods were updated to be consistent across all view integrations. Before this
release, the return types used by the ASGI and Django views were too generic.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3712](https://github.com/strawberry-graphql/strawberry/pull/3712/)


0.252.0 - 2024-11-22
--------------------

The view classes of all integrations now have a `decode_json` method that allows
you to customize the decoding of HTTP JSON requests.

This is useful if you want to use a different JSON decoder, for example, to
optimize performance.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3709](https://github.com/strawberry-graphql/strawberry/pull/3709/)


0.251.0 - 2024-11-21
--------------------

Starting with this release, the same JSON encoder is used to encode HTTP
responses and WebSocket messages.

This enables developers to override the `encode_json` method on their views to
customize the JSON encoder used by all web protocols.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3708](https://github.com/strawberry-graphql/strawberry/pull/3708/)


0.250.1 - 2024-11-19
--------------------

This release refactors part of the legacy `graphql-ws` protocol implementation, making it easier to read, maintain, and extend.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3704](https://github.com/strawberry-graphql/strawberry/pull/3704/)


0.250.0 - 2024-11-18
--------------------

In this release, we migrated the `graphql-transport-ws` types from data classes to typed dicts.
Using typed dicts enabled us to precisely model `null` versus `undefined` values, which are common in that protocol.
As a result, we could remove custom conversion methods handling these cases and simplify the codebase.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3701](https://github.com/strawberry-graphql/strawberry/pull/3701/)


0.249.0 - 2024-11-18
--------------------

After a year-long deprecation period, the `SentryTracingExtension` has been
removed in favor of the official Sentry SDK integration.

To migrate, remove the `SentryTracingExtension` from your Strawberry schema and
then follow the
[official Sentry SDK integration guide](https://docs.sentry.io/platforms/python/integrations/strawberry/).

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3672](https://github.com/strawberry-graphql/strawberry/pull/3672/)


0.248.1 - 2024-11-08
--------------------

This release fixes the following deprecation warning:

```
Failing to pass a value to the 'type_params' parameter of 'typing._eval_type' is deprecated,
as it leads to incorrect behaviour when calling typing._eval_type on a stringified annotation
that references a PEP 695 type parameter. It will be disallowed in Python 3.15.
```

This was only trigger in Python 3.13 and above.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3692](https://github.com/strawberry-graphql/strawberry/pull/3692/)


0.248.0 - 2024-11-07
--------------------

In this release, all types of the legacy graphql-ws protocol were refactored.
The types are now much stricter and precisely model the difference between null and undefined fields.
As a result, our protocol implementation and related tests are now more robust and easier to maintain.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3689](https://github.com/strawberry-graphql/strawberry/pull/3689/)


0.247.2 - 2024-11-05
--------------------

This release fixes the issue that some coroutines in the WebSocket protocol handlers were never awaited if clients disconnected shortly after starting an operation.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3687](https://github.com/strawberry-graphql/strawberry/pull/3687/)


0.247.1 - 2024-11-01
--------------------

Starting with this release, both websocket-based protocols will handle unexpected socket disconnections more gracefully.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3685](https://github.com/strawberry-graphql/strawberry/pull/3685/)


0.247.0 - 2024-10-21
--------------------

This release fixes a regression in the legacy GraphQL over WebSocket protocol.
Legacy protocol implementations should ignore client message parsing errors.
During a recent refactor, Strawberry changed this behavior to match the new protocol, where parsing errors must close the WebSocket connection.
The expected behavior is restored and adequately tested in this release.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3670](https://github.com/strawberry-graphql/strawberry/pull/3670/)


0.246.3 - 2024-10-21
--------------------

This release addresses a bug where directives were being added multiple times when defined in an interface which multiple objects inherits from.

The fix involves deduplicating directives when applying extensions/permissions to a field, ensuring that each directive is only added once.

Contributed by [Arthur](https://github.com/Speedy1991) via [PR #3674](https://github.com/strawberry-graphql/strawberry/pull/3674/)


0.246.2 - 2024-10-12
--------------------

This release tweaks the Flask integration's `render_graphql_ide` method to be stricter typed internally, making type checkers ever so slightly happier.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3666](https://github.com/strawberry-graphql/strawberry/pull/3666/)


0.246.1 - 2024-10-09
--------------------

This release adds support for using raw Python enum types in your schema
(enums that are not decorated with `@strawberry.enum`)

This is useful if you have enum types from other places in your code
that you want to use in strawberry.
i.e
```py
# somewhere.py
from enum import Enum


class AnimalKind(Enum):
    AXOLOTL, CAPYBARA = range(2)


# gql/animals
from somewhere import AnimalKind


@strawberry.type
class AnimalType:
    kind: AnimalKind
```

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #3639](https://github.com/strawberry-graphql/strawberry/pull/3639/)


0.246.0 - 2024-10-07
--------------------

The AIOHTTP, ASGI, and Django test clients' `asserts_errors` option has been renamed to `assert_no_errors` to better reflect its purpose.
This change is backwards-compatible, but the old option name will raise a deprecation warning.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3661](https://github.com/strawberry-graphql/strawberry/pull/3661/)


0.245.0 - 2024-10-07
--------------------

This release removes the dated `subscriptions_enabled` setting from the Django and Channels integrations.
Instead, WebSocket support is now enabled by default in all GraphQL IDEs.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3660](https://github.com/strawberry-graphql/strawberry/pull/3660/)


0.244.1 - 2024-10-06
--------------------

Fixes an issue where the codegen tool would crash when working with a nullable list of types.

Contributed by [Jacob Allen](https://github.com/enoua5) via [PR #3653](https://github.com/strawberry-graphql/strawberry/pull/3653/)


0.244.0 - 2024-10-05
--------------------

Starting with this release, WebSocket logic now lives in the base class shared between all HTTP integrations.
This makes the behaviour of WebSockets much more consistent between integrations and easier to maintain.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3638](https://github.com/strawberry-graphql/strawberry/pull/3638/)


0.243.1 - 2024-09-26
--------------------

This releases adds support for Pydantic 2.9.0's Mypy plugin

Contributed by [Krisque](https://github.com/chrisemke) via [PR #3632](https://github.com/strawberry-graphql/strawberry/pull/3632/)


0.243.0 - 2024-09-25
--------------------

Starting with this release, multipart uploads are disabled by default and Strawberry Django view is no longer implicitly exempted from Django's CSRF protection.
Both changes relieve users from implicit security implications inherited from the GraphQL multipart request specification which was enabled in Strawberry by default.

These are breaking changes if you are using multipart uploads OR the Strawberry Django view.
Migrations guides including further information are available on the Strawberry website.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3645](https://github.com/strawberry-graphql/strawberry/pull/3645/)


0.242.0 - 2024-09-19
--------------------

Starting with this release, clients using the legacy graphql-ws subprotocol will receive an error when they try to send binary data frames.
Before, binary data frames were silently ignored.

While vaguely defined in the protocol, the legacy graphql-ws subprotocol is generally understood to only support text data frames.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3633](https://github.com/strawberry-graphql/strawberry/pull/3633/)


0.241.0 - 2024-09-16
--------------------

You can now configure your schemas to provide a custom subclass of
`strawberry.types.Info` to your types and queries.

```py
import strawberry
from strawberry.schema.config import StrawberryConfig

from .models import ProductModel


class CustomInfo(strawberry.Info):
    @property
    def selected_group_id(self) -> int | None:
        """Get the ID of the group you're logged in as."""
        return self.context["request"].headers.get("Group-ID")


@strawberry.type
class Group:
    id: strawberry.ID
    name: str


@strawberry.type
class User:
    id: strawberry.ID
    name: str
    group: Group


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: strawberry.ID, info: CustomInfo) -> Product:
        kwargs = {"id": id, "name": ...}

        if info.selected_group_id is not None:
            # Get information about the group you're a part of, if
            # available.
            kwargs["group"] = ...

        return User(**kwargs)


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(info_class=CustomInfo),
)
```

Contributed by [Ethan Henderson](https://github.com/parafoxia) via [PR #3592](https://github.com/strawberry-graphql/strawberry/pull/3592/)


0.240.4 - 2024-09-13
--------------------

This release fixes how we check for multipart subscriptions to be
in line with the latest changes in the spec.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3627](https://github.com/strawberry-graphql/strawberry/pull/3627/)


0.240.3 - 2024-09-12
--------------------

This release fixes an issue that prevented extensions to receive the result from
the execution context when executing operations in async.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #3629](https://github.com/strawberry-graphql/strawberry/pull/3629/)


0.240.2 - 2024-09-11
--------------------

This release updates how we check for GraphQL core's version to remove a
dependency on the `packaging` package.

Contributed by [Nicholas Bollweg](https://github.com/bollwyvl) via [PR #3622](https://github.com/strawberry-graphql/strawberry/pull/3622/)


0.240.1 - 2024-09-11
--------------------

This release adds support for Python 3.13 (which will be out soon!)

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3510](https://github.com/strawberry-graphql/strawberry/pull/3510/)


0.240.0 - 2024-09-10
--------------------

This release adds support for schema-extensions in subscriptions.

Here's a small example of how to use them (they work the same way as query and
mutation extensions):

```python
import asyncio
from typing import AsyncIterator

import strawberry
from strawberry.extensions.base_extension import SchemaExtension


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def notifications(self, info: strawberry.Info) -> AsyncIterator[str]:
        for _ in range(3):
            yield "Hello"


class MyExtension(SchemaExtension):
    async def on_operation(self):
        # This would run when the subscription starts
        print("Subscription started")
        yield
        # The subscription has ended
        print("Subscription ended")


schema = strawberry.Schema(
    query=Query, subscription=Subscription, extensions=[MyExtension]
)
```

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #3554](https://github.com/strawberry-graphql/strawberry/pull/3554/)


0.239.2 - 2024-09-03
--------------------

This release fixes a TypeError on Python 3.8 due to us using a
`asyncio.Queue[Tuple[bool, Any]](1)` instead of `asyncio.Queue(1)`.

Contributed by [Daniel Szoke](https://github.com/szokeasaurusrex) via [PR #3615](https://github.com/strawberry-graphql/strawberry/pull/3615/)


0.239.1 - 2024-09-02
--------------------

This release fixes an issue with the http multipart subscription where the
status code would be returned as `None`, instead of 200.

We also took the opportunity to update the internals to better support
additional protocols in future.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3610](https://github.com/strawberry-graphql/strawberry/pull/3610/)


0.239.0 - 2024-08-31
--------------------

This release adds support for multipart subscriptions in almost all[^1] of our
http integrations!

[Multipart subcriptions](https://www.apollographql.com/docs/router/executing-operations/subscription-multipart-protocol/)
are a new protocol from Apollo GraphQL, built on the
[Incremental Delivery over HTTP spec](https://github.com/graphql/graphql-over-http/blob/main/rfcs/IncrementalDelivery.md),
which is also used for `@defer` and `@stream`.

The main advantage of this protocol is that when using the Apollo Client
libraries you don't need to install any additional dependency, but in future
this feature should make it easier for us to implement `@defer` and `@stream`

Also, this means that you don't need to use Django Channels for subscription,
since this protocol is based on HTTP we don't need to use websockets.

[^1]: Flask, Chalice and the sync Django integration don't support this.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3076](https://github.com/strawberry-graphql/strawberry/pull/3076/)


0.238.1 - 2024-08-30
--------------------

Fix an issue where `StrawberryResolver.is_async` was returning `False` for a
function decorated with asgiref's `@sync_to_async`.

The root cause is that in python >= 3.12 coroutine functions are market using
`inspect.markcoroutinefunction`, which should be checked with
`inspect.iscoroutinefunction` instead of `asyncio.iscoroutinefunction`

Contributed by [Hyun S. Moon](https://github.com/shmoon-kr) via [PR #3599](https://github.com/strawberry-graphql/strawberry/pull/3599/)


0.238.0 - 2024-08-30
--------------------

This release removes the integration of Starlite, as it
has been deprecated since 11 May 2024.

If you are using Starlite, please consider migrating to Litestar (https://litestar.dev) or another alternative.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3609](https://github.com/strawberry-graphql/strawberry/pull/3609/)


0.237.3 - 2024-07-31
--------------------

This release fixes the type of the ASGI request handler's `scope` argument, making type checkers ever so slightly happier.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3581](https://github.com/strawberry-graphql/strawberry/pull/3581/)


0.237.2 - 2024-07-26
--------------------

This release makes the ASGI and FastAPI integrations share their HTTP request adapter code, making Strawberry ever so slightly smaller and easier to maintain.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3582](https://github.com/strawberry-graphql/strawberry/pull/3582/)


0.237.1 - 2024-07-24
--------------------

This release adds support for GraphQL-core v3.3 (which has not yet been
released). Note that we continue to support GraphQL-core v3.2 as well.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #3570](https://github.com/strawberry-graphql/strawberry/pull/3570/)


0.237.0 - 2024-07-24
--------------------

This release ensures using pydantic 2.8.0 doesn't break when using experimental
pydantic_type and running mypy.

Contributed by [Martin Roy](https://github.com/lindycoder) via [PR #3562](https://github.com/strawberry-graphql/strawberry/pull/3562/)


0.236.2 - 2024-07-23
--------------------

Update federation entity resolver exception handling to set the result to the original error instead of a `GraphQLError`, which obscured the original message and meta-fields.

Contributed by [Bradley Oesch](https://github.com/bradleyoesch) via [PR #3144](https://github.com/strawberry-graphql/strawberry/pull/3144/)


0.236.1 - 2024-07-23
--------------------

This release fixes an issue where optional lazy types using `| None` were
failing to be correctly resolved inside modules using future annotations, e.g.

```python
from __future__ import annotations

from typing import Annotated, TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from types import Group


@strawberry.type
class Person:
    group: Annotated["Group", strawberry.lazy("types.group")] | None
```

This should now work as expected.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3576](https://github.com/strawberry-graphql/strawberry/pull/3576/)


0.236.0 - 2024-07-17
--------------------

This release changes some of the internals of Strawberry, it shouldn't
be affecting most of the users, but since we have changed the structure
of the code you might need to update your imports.

Thankfully we also provide a codemod for this, you can run it with:

```bash
strawberry upgrade update-imports
```

This release also includes additional documentation to some of
the classes, methods and functions, this is in preparation for
having the API reference in the documentation ✨

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3546](https://github.com/strawberry-graphql/strawberry/pull/3546/)


0.235.2 - 2024-07-08
--------------------

This release removes an unnecessary check from our internal GET query parsing logic making it simpler and (insignificantly) faster.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3558](https://github.com/strawberry-graphql/strawberry/pull/3558/)


0.235.1 - 2024-06-26
--------------------

This release improves the performance when returning a lot of data, especially
when using generic inputs (where we got a 7x speedup in our benchmark!).

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3549](https://github.com/strawberry-graphql/strawberry/pull/3549/)


0.235.0 - 2024-06-10
--------------------

This release adds a new configuration to disable field suggestions in the error
response.

```python
@strawberry.type
class Query:
    name: str


schema = strawberry.Schema(
    query=Query, config=StrawberryConfig(disable_field_suggestions=True)
)
```

Trying to query `{ nam }` will not suggest to query `name` instead.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3537](https://github.com/strawberry-graphql/strawberry/pull/3537/)


0.234.3 - 2024-06-10
--------------------

Fixes a bug where pydantic models as the default value for an input did not print the proper schema.
See [this issue](https://github.com/strawberry-graphql/strawberry/issues/3285).

Contributed by [ppease](https://github.com/ppease) via [PR #3499](https://github.com/strawberry-graphql/strawberry/pull/3499/)


0.234.2 - 2024-06-07
--------------------

This release fixes an issue when trying to retrieve specialized type vars from a
generic type that has been aliased to a name, in cases like:

```python
@strawberry.type
class Fruit(Generic[T]): ...


SpecializedFruit = Fruit[str]
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3535](https://github.com/strawberry-graphql/strawberry/pull/3535/)


0.234.1 - 2024-06-06
--------------------

Improved error message when supplying GlobalID with invalid or unknown type name component

Contributed by [Take Weiland](https://github.com/diesieben07) via [PR #3533](https://github.com/strawberry-graphql/strawberry/pull/3533/)


0.234.0 - 2024-06-01
--------------------

This release separates the `relay.ListConnection` logic that calculates the
slice of the nodes into a separate function.

This allows for easier reuse of that logic for other places/libraries.

The new function lives in the `strawberry.relay.utils` and can be used by
calling `SliceMetadata.from_arguments`.

This has no implications to end users.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3530](https://github.com/strawberry-graphql/strawberry/pull/3530/)


0.233.3 - 2024-05-31
--------------------

This release fixes a typing issue where trying to type a `root` argument with
`strawberry.Parent` would fail, like in the following example:

```python
import strawberry


@strawberry.type
class SomeType:
    @strawberry.field
    def hello(self, root: strawberry.Parent[str]) -> str:
        return "world"
```

This should now work as intended.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3529](https://github.com/strawberry-graphql/strawberry/pull/3529/)


0.233.2 - 2024-05-31
--------------------

This release fixes an introspection issue when requesting `isOneOf` on built-in
scalars, like `String`.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3528](https://github.com/strawberry-graphql/strawberry/pull/3528/)


0.233.1 - 2024-05-30
--------------------

This release exposes `get_arguments` in the schema_converter module to allow
integrations, such as strawberry-django, to reuse that functionality if needed.

This is an internal change with no impact for end users.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3527](https://github.com/strawberry-graphql/strawberry/pull/3527/)


0.233.0 - 2024-05-29
--------------------

This release refactors our Federation integration to create types using
Strawberry directly, instead of using low level types from GraphQL-core.

The only user facing change is that now the `info` object passed to the
`resolve_reference` function is the `strawberry.Info` object instead of the one
coming coming from GraphQL-core. This is a **breaking change** for users that
were using the `info` object directly.

If you need to access the original `info` object you can do so by accessing the
`_raw_info` attribute.

```python
import strawberry


@strawberry.federation.type(keys=["upc"])
class Product:
    upc: str

    @classmethod
    def resolve_reference(cls, info: strawberry.Info, upc: str) -> "Product":
        # Access the original info object
        original_info = info._raw_info

        return Product(upc=upc)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3525](https://github.com/strawberry-graphql/strawberry/pull/3525/)


0.232.2 - 2024-05-28
--------------------

This release fixes an issue that would prevent using lazy aliased connections to
annotate a connection field.

For example, this should now work correctly:

```python
# types.py


@strawberry.type
class Fruit: ...


FruitConnection: TypeAlias = ListConnection[Fruit]
```

```python
# schema.py


@strawberry.type
class Query:
    fruits: Annotated["FruitConnection", strawberry.lazy("types")] = (
        strawberry.connection()
    )
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3524](https://github.com/strawberry-graphql/strawberry/pull/3524/)


0.232.1 - 2024-05-27
--------------------

This release fixes an issue where mypy would complain when using a typed async
resolver with `strawberry.field(resolver=...)`.

Now the code will type check correctly. We also updated our test suite to make
we catch similar issues in the future.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3516](https://github.com/strawberry-graphql/strawberry/pull/3516/)


0.232.0 - 2024-05-25
--------------------

This release improves type checking for async resolver functions when used as
`strawberry.field(resolver=resolver_func)`.

Now doing this will raise a type error:

```python
import strawberry


def some_resolver() -> int:
    return 0


@strawberry.type
class User:
    # Note the field being typed as str instead of int
    name: str = strawberry.field(resolver=some_resolver)
```

Contributed by [Bryan Ricker](https://github.com/bricker) via [PR #3241](https://github.com/strawberry-graphql/strawberry/pull/3241/)


0.231.1 - 2024-05-25
--------------------

Fixes an issue where lazy annotations raised an error when used together with a List

Contributed by [jeich](https://github.com/jeich) via [PR #3388](https://github.com/strawberry-graphql/strawberry/pull/3388/)


0.231.0 - 2024-05-25
--------------------

When calling the CLI without all the necessary dependencies installed,
a `MissingOptionalDependenciesError` will be raised instead of a
`ModuleNotFoundError`. This new exception will provide a more helpful
hint regarding how to fix the problem.

Contributed by [Ethan Henderson](https://github.com/parafoxia) via [PR #3511](https://github.com/strawberry-graphql/strawberry/pull/3511/)


0.230.0 - 2024-05-22
--------------------

This release adds support for `@oneOf` on input types! 🎉 You can use
`one_of=True` on input types to create an input type that should only have one
of the fields set.

```python
import strawberry


@strawberry.input(one_of=True)
class ExampleInputTagged:
    a: str | None = strawberry.UNSET
    b: int | None = strawberry.UNSET
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3429](https://github.com/strawberry-graphql/strawberry/pull/3429/)


0.229.2 - 2024-05-22
--------------------

This release fixes an issue when using `Annotated` + `strawberry.lazy` +
deferred annotations such as:

```python
from __future__ import annotations
import strawberry
from typing import Annotated


@strawberry.type
class Query:
    a: Annotated["datetime", strawberry.lazy("datetime")]


schema = strawberry.Schema(Query)
```

Before this would only work if `datetime` was not inside quotes. Now it should
work as expected!

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3507](https://github.com/strawberry-graphql/strawberry/pull/3507/)


0.229.1 - 2024-05-15
--------------------

This release fixes a regression from 0.229.0 where using a generic interface
inside a union would return an error.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3502](https://github.com/strawberry-graphql/strawberry/pull/3502/)


0.229.0 - 2024-05-12
--------------------

This release improves our support for generic types, now using the same the same
generic multiple times with a list inside an interface or union is supported,
for example the following will work:

```python
import strawberry


@strawberry.type
class BlockRow[T]:
    items: list[T]


@strawberry.type
class Query:
    @strawberry.field
    def blocks(self) -> list[BlockRow[str] | BlockRow[int]]:
        return [
            BlockRow(items=["a", "b", "c"]),
            BlockRow(items=[1, 2, 3, 4]),
        ]


schema = strawberry.Schema(query=Query)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3463](https://github.com/strawberry-graphql/strawberry/pull/3463/)


0.228.0 - 2024-05-12
--------------------

This releases updates the JSON scalar definition to have the updated `specifiedBy` URL.

The release is marked as minor because it will change the generated schema if you're using the JSON scalar.

Contributed by [Egor](https://github.com/Birdi7) via [PR #3478](https://github.com/strawberry-graphql/strawberry/pull/3478/)


0.227.7 - 2024-05-12
--------------------

This releases updates the `field-extensions` documentation's `StrawberryField` stability warning to include stable features.

The release is marked as patch because it only changes documentation.

Contributed by [Ray Sy](https://github.com/fireteam99) via [PR #3496](https://github.com/strawberry-graphql/strawberry/pull/3496/)


0.227.6 - 2024-05-11
--------------------

Fix `AssertionError` caused by the `DatadogTracingExtension` whenever the query is unavailable.

The bug in question was reported by issue [#3150](https://github.com/strawberry-graphql/strawberry/issues/3150).
The datadog extension would throw an `AssertionError` whenever there was no query available. This could happen if,
for example, a user POSTed something to `/graphql` with a JSON that doesn't contain a `query` field as per the
GraphQL spec.

The fix consists of adding `query_missing` to the `operation_type` tag, and also adding `query_missing` to the resource name.
It also makes it easier to look for logs of users making invalid queries by searching for `query_missing` in Datadog.

Contributed by [Lucas Valente](https://github.com/serramatutu) via [PR #3483](https://github.com/strawberry-graphql/strawberry/pull/3483/)


0.227.5 - 2024-05-11
--------------------

**Deprecations:** This release deprecates the `Starlite` integration in favour of the `LiteStar` integration.
Refer to the [LiteStar](./litestar.md) integration for more information.
LiteStar is a [renamed](https://litestar.dev/about/organization.html#litestar-and-starlite) and upgraded version of Starlite.

Before:

```python
from strawberry.starlite import make_graphql_controller
```

After:

```python
from strawberry.litestar import make_graphql_controller
```

Contributed by [Egor](https://github.com/Birdi7) via [PR #3492](https://github.com/strawberry-graphql/strawberry/pull/3492/)


0.227.4 - 2024-05-09
--------------------

This release fixes a bug in release 0.227.3 where FragmentSpread nodes
were not resolving edges.

Contributed by [Eric Uriostigue](https://github.com/euriostigue) via [PR #3487](https://github.com/strawberry-graphql/strawberry/pull/3487/)


0.227.3 - 2024-05-01
--------------------

This release adds an optimization to `ListConnection` such that only queries with
`edges` or `pageInfo` in their selected fields triggers `resolve_edges`.

This change is particularly useful for the `strawberry-django` extension's
`ListConnectionWithTotalCount` and the only selected field is `totalCount`. An
extraneous SQL query is prevented with this optimization.

Contributed by [Eric Uriostigue](https://github.com/euriostigue) via [PR #3480](https://github.com/strawberry-graphql/strawberry/pull/3480/)


0.227.2 - 2024-04-21
--------------------

This release fixes a minor issue where the docstring for the relay util `to_base64` described the return type incorrectly.

Contributed by [Gavin Bannerman](https://github.com/gbannerman) via [PR #3467](https://github.com/strawberry-graphql/strawberry/pull/3467/)


0.227.1 - 2024-04-20
--------------------

This release fixes an issue where annotations on `@strawberry.type`s were overridden
by our code. With release all annotations should be preserved.

This is useful for libraries that use annotations to introspect Strawberry types.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3003](https://github.com/strawberry-graphql/strawberry/pull/3003/)


0.227.0 - 2024-04-19
--------------------

This release improves the schema codegen, making it more robust and easier to
use.

It does this by introducing a directed acyclic graph for the schema codegen,
which should reduce the amount of edits needed to make the generated code work,
since it will be able to generate the code in the correct order (based on the
dependencies of each type).

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3116](https://github.com/strawberry-graphql/strawberry/pull/3116/)


0.226.2 - 2024-04-19
--------------------

This release updates our Mypy plugin to add support for Pydantic >= 2.7.0

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3462](https://github.com/strawberry-graphql/strawberry/pull/3462/)


0.226.1 - 2024-04-19
--------------------

This releases fixes a bug in the mypy plugin where the `from_pydantic` method
was not correctly typed.

Contributed by [Corentin-Br](https://github.com/Corentin-Br) via [PR #3368](https://github.com/strawberry-graphql/strawberry/pull/3368/)


0.226.0 - 2024-04-17
--------------------

Starting with this release, any error raised from within schema
extensions will abort the operation and is returned to the client.

This corresponds to the way we already handle field extension errors
and resolver errors.

This is particular useful for schema extensions performing checks early
in the request lifecycle, for example:

```python
class MaxQueryLengthExtension(SchemaExtension):
    MAX_QUERY_LENGTH = 8192

    async def on_operation(self):
        if len(self.execution_context.query) > self.MAX_QUERY_LENGTH:
            raise StrawberryGraphQLError(message="Query too large")
        yield
```

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #3217](https://github.com/strawberry-graphql/strawberry/pull/3217/)


0.225.1 - 2024-04-15
--------------------

This change fixes GET request queries returning a 400 if a content_type header is supplied

Contributed by [Nathan John](https://github.com/vethan) via [PR #3452](https://github.com/strawberry-graphql/strawberry/pull/3452/)


0.225.0 - 2024-04-14
--------------------

This release adds support for using FastAPI APIRouter arguments in GraphQLRouter.

Now you have the opportunity to specify parameters such as `tags`, `route_class`,
`deprecated`, `include_in_schema`, etc:

```python
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(schema, tags=["graphql"])

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

Contributed by [Nikita Paramonov](https://github.com/nparamonov) via [PR #3442](https://github.com/strawberry-graphql/strawberry/pull/3442/)


0.224.2 - 2024-04-13
--------------------

This releases fixes a bug where schema extensions where not running a LIFO order.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #3416](https://github.com/strawberry-graphql/strawberry/pull/3416/)


0.224.1 - 2024-03-30
--------------------

This release fixes a deprecation warning when using the Apollo Tracing
Extension.

Contributed by [A. Coady](https://github.com/coady) via [PR #3410](https://github.com/strawberry-graphql/strawberry/pull/3410/)


0.224.0 - 2024-03-30
--------------------

This release adds support for using both Pydantic v1 and v2, when importing from
`pydantic.v1`.

This is automatically detected and the correct version is used.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3426](https://github.com/strawberry-graphql/strawberry/pull/3426/)


0.223.0 - 2024-03-29
--------------------

This release adds support for Apollo Federation in the schema codegen. Now you
can convert a schema like this:

```graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.3",
        import: ["@key", "@shareable"])

type Query {
  me: User
}

type User @key(fields: "id") {
  id: ID!
  username: String! @shareable
}
```

to a Strawberry powered schema like this:

```python
import strawberry


@strawberry.type
class Query:
    me: User | None


@strawberry.federation.type(keys=["id"])
class User:
    id: strawberry.ID
    username: str = strawberry.federation.field(shareable=True)


schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)
```

By running the following command:

```bash
strawberry schema-codegen example.graphql
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3417](https://github.com/strawberry-graphql/strawberry/pull/3417/)


0.222.0 - 2024-03-27
--------------------

This release adds support for Apollo Federation v2.7 which includes the `@authenticated`, `@requiresScopes`, `@policy` directives, as well as the `label` argument for `@override`.
As usual, we have first class support for them in the `strawberry.federation` namespace, here's an example:

```python
from strawberry.federation.schema_directives import Override


@strawberry.federation.type(
    authenticated=True,
    policy=[["client", "poweruser"], ["admin"]],
    requires_scopes=[["client", "poweruser"], ["admin"]],
)
class Product:
    upc: str = strawberry.federation.field(
        override=Override(override_from="mySubGraph", label="percent(1)")
    )
```

Contributed by [Tyger Taco](https://github.com/TygerTaco) via [PR #3420](https://github.com/strawberry-graphql/strawberry/pull/3420/)


0.221.1 - 2024-03-21
--------------------

This release properly allows passing one argument to the `Info` class.

This is now fully supported:

```python
import strawberry

from typing import TypedDict


class Context(TypedDict):
    user_id: str


@strawberry.type
class Query:
    @strawberry.field
    def info(self, info: strawberry.Info[Context]) -> str:
        return info.context["user_id"]
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3419](https://github.com/strawberry-graphql/strawberry/pull/3419/)


0.221.0 - 2024-03-21
--------------------

This release improves the `Info` type, by adding support for default TypeVars
and by exporting it from the main module. This makes it easier to use `Info` in
your own code, without having to import it from `strawberry.types.info`.

### New export

By exporting `Info` from the main module, now you can do the follwing:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def info(self, info: strawberry.Info) -> str:
        # do something with info
        return "hello"
```

### Default TypeVars

The `Info` type now has default TypeVars, so you can use it without having to
specify the type arguments, like we did in the example above. Make sure to use
the latest version of Mypy or Pyright for this. It also means that you can only
pass one value to it if you only care about the context type:

```python
import strawberry

from .context import Context


@strawberry.type
class Query:
    @strawberry.field
    def info(self, info: strawberry.Info[Context]) -> str:
        return info.context.user_id
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3418](https://github.com/strawberry-graphql/strawberry/pull/3418/)


0.220.0 - 2024-03-08
--------------------

This release adds support to allow passing `connection_params` as dictionary to `GraphQLWebsocketCommunicator` class when testing [channels integration](https://strawberry.rocks/docs/integrations/channels#testing)


### Example


```python
GraphQLWebsocketCommunicator(
    application=application,
    path="/graphql",
    connection_params={"username": "strawberry"},
)
```

Contributed by [selvarajrajkanna](https://github.com/selvarajrajkanna) via [PR #3403](https://github.com/strawberry-graphql/strawberry/pull/3403/)


0.219.2 - 2024-02-06
--------------------

This releases updates the dependency of `python-multipart` to be at least `0.0.7` (which includes a security fix).

It also removes the upper bound for `python-multipart` so you can always install the latest version (if compatible) 😊

Contributed by [Srikanth](https://github.com/XChikuX) via [PR #3375](https://github.com/strawberry-graphql/strawberry/pull/3375/)


0.219.1 - 2024-01-28
--------------------

- Improved error message when supplying in incorrect before or after argument with using relay and pagination.
- Add extra PR requirement in README.md

Contributed by [SD](https://github.com/sdobbelaere) via [PR #3361](https://github.com/strawberry-graphql/strawberry/pull/3361/)


0.219.0 - 2024-01-24
--------------------

This release adds support for [litestar](https://litestar.dev/).

```python
import strawberry
from litestar import Request, Litestar
from strawberry.litestar import make_graphql_controller
from strawberry.types.info import Info


def custom_context_getter(request: Request):
    return {"custom": "context"}


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info: strawberry.Info[object, None]) -> str:
        return info.context["custom"]


schema = strawberry.Schema(Query)


GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=custom_context_getter,
)

app = Litestar(
    route_handlers=[GraphQLController],
)
```

Contributed by [Matthieu MN](https://github.com/gazorby) via [PR #3213](https://github.com/strawberry-graphql/strawberry/pull/3213/)


0.218.1 - 2024-01-23
--------------------

This release fixes a small issue in the GraphQL Transport websocket
where the connection would fail when receiving extra parameters
in the payload sent from the client.

This would happen when using Apollo Sandbox.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3356](https://github.com/strawberry-graphql/strawberry/pull/3356/)


0.218.0 - 2024-01-22
--------------------

This release adds a new method `get_fields` on the `Schema` class.
You can use `get_fields` to hide certain field based on some conditions,
for example:

```python
@strawberry.type
class User:
    name: str
    email: str = strawberry.field(metadata={"tags": ["internal"]})


@strawberry.type
class Query:
    user: User


def public_field_filter(field: StrawberryField) -> bool:
    return "internal" not in field.metadata.get("tags", [])


class PublicSchema(strawberry.Schema):
    def get_fields(
        self, type_definition: StrawberryObjectDefinition
    ) -> List[StrawberryField]:
        return list(filter(public_field_filter, type_definition.fields))


schema = PublicSchema(query=Query)
```

The schema here would only have the `name` field on the `User` type.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3274](https://github.com/strawberry-graphql/strawberry/pull/3274/)


0.217.1 - 2024-01-04
--------------------

This hotfix enables permission extensions to be used with AsyncGenerators.

Contributed by [Erik Wrede](https://github.com/erikwrede) via [PR #3318](https://github.com/strawberry-graphql/strawberry/pull/3318/)


0.217.0 - 2023-12-18
--------------------

Permissions classes now use a `FieldExtension`. The new preferred way to add permissions
is to use the `PermissionsExtension` class:

```python
import strawberry
from strawberry.permission import PermissionExtension, BasePermission


class IsAuthorized(BasePermission):
    message = "User is not authorized"
    error_extensions = {"code": "UNAUTHORIZED"}

    def has_permission(self, source, info, **kwargs) -> bool:
        return False


@strawberry.type
class Query:
    @strawberry.field(extensions=[PermissionExtension(permissions=[IsAuthorized()])])
    def name(self) -> str:
        return "ABC"
```

The old way of adding permissions using `permission_classes` is still
supported via the automatic addition of a `PermissionExtension` on the field.

### ⚠️ Breaking changes

Previously the `kwargs` argument keys for the `has_permission` method were
using camel casing (depending on your schema configuration), now they will
always follow the python name defined in your resolvers.

```python
class IsAuthorized(BasePermission):
    message = "User is not authorized"

    def has_permission(
        self, source, info, **kwargs: typing.Any
    ) -> bool:  # pragma: no cover
        # kwargs will have a key called "a_key"
        # instead of `aKey`

        return False


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthorized])
    def name(self, a_key: str) -> str:  # pragma: no cover
        return "Erik"
```

Using the new `PermissionExtension` API, permissions support even more features:

#### Silent errors

To return `None` or `[]` instead of raising an error, the `fail_silently ` keyword
argument on `PermissionExtension` can be set to `True`.

#### Custom Error Extensions & classes

Permissions will now automatically add pre-defined error extensions to the error, and
can use a custom `GraphQLError` class. This can be configured by modifying
the  `error_class` and `error_extensions` attributes on the `BasePermission` class.

#### Customizable Error Handling

To customize the error handling, the `on_unauthorized` method on
the `BasePermission` class can be used. Further changes can be implemented by
subclassing the `PermissionExtension` class.

#### Schema Directives

Permissions will automatically be added as schema directives to the schema. This
behavior can be altered by setting the `add_directives` to `False`
on `PermissionExtension`, or by setting the `_schema_directive` class attribute of the
permission to a custom directive.

Contributed by [Erik Wrede](https://github.com/erikwrede) via [PR #2570](https://github.com/strawberry-graphql/strawberry/pull/2570/)


0.216.1 - 2023-12-12
--------------------

Don't require `NodeId` annotation if resolve_id is overwritten on `Node` implemented types

Contributed by [Alexander](https://github.com/devkral) via [PR #2844](https://github.com/strawberry-graphql/strawberry/pull/2844/)


0.216.0 - 2023-12-06
--------------------

Override encode_json() method in Django BaseView to use DjangoJSONEncoder

Contributed by [Noam Stolero](https://github.com/noamsto) via [PR #3273](https://github.com/strawberry-graphql/strawberry/pull/3273/)


0.215.3 - 2023-12-06
--------------------

Fixed the base view so it uses `parse_json` when loading parameters from the query string instead of `json.loads`.

Contributed by [Elias Gabriel](https://github.com/thearchitector) via [PR #3272](https://github.com/strawberry-graphql/strawberry/pull/3272/)


0.215.2 - 2023-12-05
--------------------

This release updates the Apollo Sandbox integration to all you to
pass cookies to the GraphQL endpoint by enabling the **Include cookes**
option in the Sandbox settings.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3278](https://github.com/strawberry-graphql/strawberry/pull/3278/)


0.215.1 - 2023-11-20
--------------------

Improved error message when supplying GlobalID format that relates to another type than the query itself.

Contributed by [SD](https://github.com/sdobbelaere) via [PR #3194](https://github.com/strawberry-graphql/strawberry/pull/3194/)


0.215.0 - 2023-11-19
--------------------

Adds an optional `extensions` parameter to `strawberry.federation.field`, with default value `None`. The key is passed through to `strawberry.field`, so the functionality is exactly as described [here](https://strawberry.rocks/docs/guides/field-extensions).

Example:

```python
strawberry.federation.field(extensions=[InputMutationExtension()])
```

Contributed by [Bryan Ricker](https://github.com/bricker) via [PR #3239](https://github.com/strawberry-graphql/strawberry/pull/3239/)


0.214.0 - 2023-11-15
--------------------

This release updates the GraphiQL packages to their latest versions:

- `graphiql@3.0.9`
- `@graphiql/plugin-explorer@1.0.2`

Contributed by [Rodrigo Feijao](https://github.com/rodrigofeijao) via [PR #3227](https://github.com/strawberry-graphql/strawberry/pull/3227/)


0.213.0 - 2023-11-08
--------------------

This release adds support in _all_ all our HTTP integration for choosing between
different GraphQL IDEs. For now we support [GraphiQL](https://github.com/graphql/graphiql) (the default),
[Apollo Sandbox](https://www.apollographql.com/docs/graphos/explorer/sandbox/), and [Pathfinder](https://pathfinder.dev/).

**Deprecations:** This release deprecates the `graphiql` option in all HTTP integrations,
in favour of `graphql_ide`, this allows us to only have one settings to change GraphQL ide,
or to disable it.

Here's a couple of examples of how you can use this:

### FastAPI

```python
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from api.schema import schema

graphql_app = GraphQLRouter(schema, graphql_ide="apollo-sandbox")

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

### Django

```python
from django.urls import path

from strawberry.django.views import GraphQLView

from api.schema import schema

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema, graphql_ide="pathfinder")),
]
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3209](https://github.com/strawberry-graphql/strawberry/pull/3209/)


0.212.0 - 2023-11-07
--------------------

This release changes how we check for generic types. Previously, any type that
had a generic typevar would be considered generic for the GraphQL schema, this
would generate un-necessary types in some cases. Now, we only consider a type
generic if it has a typevar that is used as the type of a field or one of its arguments.

For example the following type:

```python
@strawberry.type
class Edge[T]:
    cursor: strawberry.ID
    some_interna_value: strawberry.Private[T]
```

Will not generate a generic type in the schema, as the typevar `T` is not used
as the type of a field or argument.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3202](https://github.com/strawberry-graphql/strawberry/pull/3202/)


0.211.2 - 2023-11-06
--------------------

This release removes unused `graphiql` submodules for Flask, Quart and Sanic.

Contributed by [Pierre Chapuis](https://github.com/catwell) via [PR #3203](https://github.com/strawberry-graphql/strawberry/pull/3203/)


0.211.1 - 2023-10-25
--------------------

This release fixes an issue that prevented the `parser_cache` extension to be used in combination with
other extensions such as `MaxTokensLimiter`.

The following should work as expected now:

```python
schema = strawberry.Schema(
    query=Query, extensions=[MaxTokensLimiter(max_token_count=20), ParserCache()]
)
```

Contributed by [David Šanda](https://github.com/Dazix) via [PR #3170](https://github.com/strawberry-graphql/strawberry/pull/3170/)


0.211.0 - 2023-10-24
--------------------

This release adds a Quart view.

Contributed by [Pierre Chapuis](https://github.com/catwell) via [PR #3162](https://github.com/strawberry-graphql/strawberry/pull/3162/)


0.210.0 - 2023-10-24
--------------------

This release deprecates our `SentryTracingExtension`, as it is now incorporated directly into Sentry itself as of [version 1.32.0](https://github.com/getsentry/sentry-python/releases/tag/1.32.0). You can now directly instrument Strawberry with Sentry.

Below is the revised usage example:

```python
import sentry_sdk
from sentry_sdk.integrations.strawberry import StrawberryIntegration

sentry_sdk.init(
    dsn="___PUBLIC_DSN___",
    integrations=[
        # make sure to set async_execution to False if you're executing
        # GraphQL queries synchronously
        StrawberryIntegration(async_execution=True),
    ],
    traces_sample_rate=1.0,
)
```

Many thanks to @sentrivana for their work on this integration!

0.209.8 - 2023-10-20
--------------------

Fix strawberry mypy plugin for pydantic v2

Contributed by [Corentin-Br](https://github.com/Corentin-Br) via [PR #3159](https://github.com/strawberry-graphql/strawberry/pull/3159/)


0.209.7 - 2023-10-15
--------------------

Remove stack_info from error log messages to not clutter error logging with unnecessary information.

Contributed by [Malte Finsterwalder](https://github.com/finsterwalder) via [PR #3143](https://github.com/strawberry-graphql/strawberry/pull/3143/)


0.209.6 - 2023-10-07
--------------------

Add text/html content-type to chalice graphiql response

Contributed by [Julian Popescu](https://github.com/jpopesculian) via [PR #3137](https://github.com/strawberry-graphql/strawberry/pull/3137/)


0.209.5 - 2023-10-03
--------------------

This release adds a new private hook in our HTTP views, it is called
`_handle_errors` and it is meant to be used by Sentry (or other integrations)
to handle errors without having to patch methods that could be overridden
by the users

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3127](https://github.com/strawberry-graphql/strawberry/pull/3127/)


0.209.4 - 2023-10-02
--------------------

This release changes how we check for conflicting resolver arguments to
exclude `self` from those checks, which were introduced on version 0.208.0.

It is a common pattern among integrations, such as the Django one, to
use `root: Model` in the resolvers for better typing inference.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3131](https://github.com/strawberry-graphql/strawberry/pull/3131/)


0.209.3 - 2023-10-02
--------------------

Mark Django's asyncview as a coroutine using `asgiref.sync.markcoroutinefunction`
to support using it with Python 3.12.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3124](https://github.com/strawberry-graphql/strawberry/pull/3124/)


0.209.2 - 2023-09-24
--------------------

Fix generation of input based on pydantic models using nested `Annotated` type annotations:

```python
import strawberry
from pydantic import BaseModel


class User(BaseModel):
    age: Optional[Annotated[int, "metadata"]]


@strawberry.experimental.pydantic.input(all_fields=True)
class UserInput:
    pass
```

Contributed by [Matthieu MN](https://github.com/gazorby) via [PR #3109](https://github.com/strawberry-graphql/strawberry/pull/3109/)


0.209.1 - 2023-09-21
--------------------

This release fixes an issue when trying to generate code from a schema that
was using double quotes inside descriptions.

The following schema will now generate code correctly:

```graphql
"""
A type of person or character within the "Star Wars" Universe.
"""
type Species {
  """
  The classification of this species, such as "mammal" or "reptile".
  """
  classification: String!
}
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3112](https://github.com/strawberry-graphql/strawberry/pull/3112/)


0.209.0 - 2023-09-19
--------------------

This release adds support for generating Strawberry types from SDL files. For example, given the following SDL file:

```graphql
type Query {
  user: User
}

type User {
  id: ID!
  name: String!
}
```

you can run

```bash
strawberry schema-codegen schema.graphql
```

to generate the following Python code:

```python
import strawberry


@strawberry.type
class Query:
    user: User | None


@strawberry.type
class User:
    id: strawberry.ID
    name: str


schema = strawberry.Schema(query=Query)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3096](https://github.com/strawberry-graphql/strawberry/pull/3096/)


0.208.3 - 2023-09-19
--------------------

Adding support for additional pydantic built in types like EmailStr or PostgresDsn.

Contributed by [ppease](https://github.com/ppease) via [PR #3101](https://github.com/strawberry-graphql/strawberry/pull/3101/)


0.208.2 - 2023-09-18
--------------------

This release fixes an issue that would prevent using generics with unnamed
unions, like in this example:

```python
from typing import Generic, TypeVar, Union
import strawberry

T = TypeVar("T")


@strawberry.type
class Connection(Generic[T]):
    nodes: list[T]


@strawberry.type
class Entity1:
    id: int


@strawberry.type
class Entity2:
    id: int


@strawberry.type
class Query:
    entities: Connection[Union[Entity1, Entity2]]
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3099](https://github.com/strawberry-graphql/strawberry/pull/3099/)


0.208.1 - 2023-09-15
--------------------

This fixes a bug where codegen would choke trying to find a field in the schema for a generic type.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #3077](https://github.com/strawberry-graphql/strawberry/pull/3077/)


0.208.0 - 2023-09-14
--------------------

Adds new strawberry.Parent type annotation to support resolvers without use of self.

E.g.

```python
@dataclass
class UserRow:
    id_: str


@strawberry.type
class User:
    @strawberry.field
    @staticmethod
    async def name(parent: strawberry.Parent[UserRow]) -> str:
        return f"User Number {parent.id_}"


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return UserRow(id_="1234")
```

Contributed by [mattalbr](https://github.com/mattalbr) via [PR #3017](https://github.com/strawberry-graphql/strawberry/pull/3017/)


0.207.1 - 2023-09-14
--------------------

This fixes a bug where codegen would choke on FragmentSpread nodes in the GraphQL during type collection.

e.g.:

```
fragment PartialBlogPost on BlogPost {
  title
}

query OperationName {
  interface {
    id
    ... on BlogPost {
      ...PartialBlogPost
    }
    ... on Image {
      url
    }
  }
}
```

The current version of the code generator is not able to handle the `...PartialBogPost` in this position because it assumes it can only find `Field` type nodes even though the spread should be legit.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #3086](https://github.com/strawberry-graphql/strawberry/pull/3086/)


0.207.0 - 2023-09-14
--------------------

This release removes the deprecated `ignore` argument from the `QueryDepthLimiter` extension.

Contributed by [Kai Benevento](https://github.com/benesgarage) via [PR #3093](https://github.com/strawberry-graphql/strawberry/pull/3093/)


0.206.0 - 2023-09-13
--------------------

`strawberry codegen` can now operate on multiple input query files.
The previous behavior of naming the file `types.js` and `types.py`
for the builtin `typescript` and `python` plugins respectively is
preserved, but only if a single query file is passed.  When more
than one query file is passed, the code generator will now use
the stem of the query file's name to construct the name of the
output files.  e.g. `my_query.graphql` -> `my_query.js` or
`my_query.py`.  Creators of custom plugins are responsible
for controlling the name of the output file themselves.  To
accomodate this, if the `__init__` method of a `QueryCodegenPlugin`
has a parameter named `query` or `query_file`, the `pathlib.Path`
to the query file will be passed to the plugin's `__init__`
method.

Finally, the `ConsolePlugin` has also recieved two new lifecycle
methods.  Unlike other `QueryCodegenPlugin`, the same instance of
the `ConsolePlugin` is used for each query file processed.  This
allows it to keep state around how many total files were processed.
The `ConsolePlugin` recieved two new lifecycle hooks: `before_any_start`
and `after_all_finished` that get called at the appropriate times.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2911](https://github.com/strawberry-graphql/strawberry/pull/2911/)


0.205.0 - 2023-08-24
--------------------

`strawberry codegen` previously choked for inputs that used the
`strawberry.UNSET` sentinal singleton value as a default.  The intent
here is to say that if a variable is not part of the request payload,
then the `UNSET` default value will not be modified and the service
code can then treat an unset value differently from a default value,
etc.

For codegen, we treat the `UNSET` default value as a `GraphQLNullValue`.
The `.value` property is the `UNSET` object in this case (instead of
the usual `None`).  In the built-in python code generator, this causes
the client to generate an object with a `None` default.  Custom client
generators can sniff at this value and update their behavior.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #3050](https://github.com/strawberry-graphql/strawberry/pull/3050/)


0.204.0 - 2023-08-15
--------------------

Adds a new flag to `export-schema` command, `--output`, which allows the user to specify the output file. If unset (current behavior), the command will continue to print to stdout.

Contributed by [Chris Hua](https://github.com/stillmatic) via [PR #3033](https://github.com/strawberry-graphql/strawberry/pull/3033/)


0.203.3 - 2023-08-14
--------------------

Mark pydantic constrained list test with need_pydantic_v1 since it is removed in pydantic V2

Contributed by [tjeerddie](https://github.com/tjeerddie) via [PR #3034](https://github.com/strawberry-graphql/strawberry/pull/3034/)


0.203.2 - 2023-08-14
--------------------

Enhancements:
- Improved pydantic conversion compatibility with specialized list classes.
  - Modified `StrawberryAnnotation._is_list` to check if the `annotation` extends from the `list` type, enabling it to be considered a list.
  - in `StrawberryAnnotation` Moved the `_is_list` check before the `_is_generic` check in `resolve` to avoid `unsupported` error in `_is_generic` before it checked `_is_list`.

This enhancement enables the usage of constrained lists as class types and allows the creation of specialized lists. The following example demonstrates this feature:

```python
import strawberry
from pydantic import BaseModel, ConstrainedList


class FriendList(ConstrainedList):
    min_items = 1


class UserModel(BaseModel):
    age: int
    friend_names: FriendList[str]


@strawberry.experimental.pydantic.type(UserModel)
class User:
    age: strawberry.auto
    friend_names: strawberry.auto
```

Contributed by [tjeerddie](https://github.com/tjeerddie) via [PR #2909](https://github.com/strawberry-graphql/strawberry/pull/2909/)


0.203.1 - 2023-08-12
--------------------

This release updates the built-in GraphiQL to the current latest version (3.0.5), it also updates React to the current latest version (18.2.0) and uses the production distribution instead of development to reduce bundle size.

Contributed by [Kien Dang](https://github.com/kiendang) via [PR #3031](https://github.com/strawberry-graphql/strawberry/pull/3031/)


0.203.0 - 2023-08-10
--------------------

Add support for extra colons in the `GlobalID` string.

Before, the string `SomeType:some:value` would produce raise an error saying that
it was expected the string to be splited in 2 parts when doing `.split(":")`.

Now we are using `.split(":", 1)`, meaning that the example above will consider
`SomeType` to be the type name, and `some:value` to be the node_id.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3025](https://github.com/strawberry-graphql/strawberry/pull/3025/)


0.202.1 - 2023-08-09
--------------------

TypingUnionType import error check is reraised because TypingGenericAlias is checked at the same time which is checked under 3.9 instead of under 3.10

Fix by separating TypingUnionType and TypingGenericAlias imports in their own try-catch

Contributed by [tjeerddie](https://github.com/tjeerddie) via [PR #3023](https://github.com/strawberry-graphql/strawberry/pull/3023/)


0.202.0 - 2023-08-08
--------------------

This release updates Strawberry's codebase to use new features in Python 3.8.
It also removes `backports.cached-property` from our dependencies, as we can
now rely on the standard library's `functools.cached_property`.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2995](https://github.com/strawberry-graphql/strawberry/pull/2995/)


0.201.1 - 2023-08-08
--------------------

Fix strawberry mypy plugin for pydantic v1

Contributed by [tjeerddie](https://github.com/tjeerddie) via [PR #3019](https://github.com/strawberry-graphql/strawberry/pull/3019/)


0.201.0 - 2023-08-08
--------------------

Fix import error in `strawberry.ext.mypy_plugin` for users who don't use pydantic.

Contributed by [David Němec](https://github.com/davidnemec) via [PR #3018](https://github.com/strawberry-graphql/strawberry/pull/3018/)


0.200.0 - 2023-08-07
--------------------

Adds initial support for pydantic V2.

This is extremely experimental for wider initial testing.

We do not encourage using this in production systems yet.

Contributed by [James Chua](https://github.com/thejaminator) via [PR #2972](https://github.com/strawberry-graphql/strawberry/pull/2972/)


0.199.3 - 2023-08-06
--------------------

This release fixes an issue on `relay.ListConnection` where async iterables that returns
non async iterable objects after being sliced where producing errors.

This should fix an issue with async strawberry-graphql-django when returning already
prefetched QuerySets.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #3014](https://github.com/strawberry-graphql/strawberry/pull/3014/)


0.199.2 - 2023-08-03
--------------------

This releases improves how we handle Annotated and async types
(used in subscriptions). Previously we weren't able to use
unions with names inside subscriptions, now that's fixed 😊

Example:

```python
@strawberry.type
class A:
    a: str


@strawberry.type
class B:
    b: str


@strawberry.type
class Query:
    x: str = "Hello"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def example_with_union(self) -> AsyncGenerator[Union[A, B], None]:
        yield A(a="Hi")
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3008](https://github.com/strawberry-graphql/strawberry/pull/3008/)


0.199.1 - 2023-08-02
--------------------

This release fixes an issue in the `graphql-ws` implementation
where sending a `null` payload would cause the connection
to be closed.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #3007](https://github.com/strawberry-graphql/strawberry/pull/3007/)


0.199.0 - 2023-08-01
--------------------

This release changes how we handle generic type vars, bringing
support to the new generic syntax in Python 3.12 (which will be out in October).

This now works:

```python
@strawberry.type
class Edge[T]:
    cursor: strawberry.ID
    node_field: T


@strawberry.type
class Query:
    @strawberry.field
    def example(self) -> Edge[int]:
        return Edge(cursor=strawberry.ID("1"), node_field=1)


schema = strawberry.Schema(query=Query)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2993](https://github.com/strawberry-graphql/strawberry/pull/2993/)


0.198.0 - 2023-07-31
--------------------

This release adds support for returning interfaces directly in resolvers:

```python
@strawberry.interface
class Node:
    id: strawberry.ID

    @classmethod
    def resolve_type(cls, obj: Any, *args: Any, **kwargs: Any) -> str:
        return "Video" if obj.id == "1" else "Image"


@strawberry.type
class Video(Node): ...


@strawberry.type
class Image(Node): ...


@strawberry.type
class Query:
    @strawberry.field
    def node(self, id: strawberry.ID) -> Node:
        return Node(id=id)


schema = strawberry.Schema(query=Query, types=[Video, Image])
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2989](https://github.com/strawberry-graphql/strawberry/pull/2989/)


0.197.0 - 2023-07-30
--------------------

This release removes support for Python 3.7 as its end of life
was on 27 Jun 2023.

This will allow us to reduce the number of CI jobs we have,
and potentially use newer features of Python. ⚡

Contributed by [Alexander](https://github.com/devkral) via [PR #2907](https://github.com/strawberry-graphql/strawberry/pull/2907/)


0.196.2 - 2023-07-28
--------------------

This release fixes an issue when trying to use `Annotated[strawberry.auto, ...]`
on python 3.10 or older, which got evident after the fix from 0.196.1.

Previously we were throwing the type away, since it usually is `Any`, but python
3.10 and older will validate that the first argument passed for `Annotated`
is callable (3.11+ does not do that anymore), and `StrawberryAuto` is not.

This changes it to keep that `Any`, which is also what someone would expect
when resolving the annotation using our custom `eval_type` function.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2990](https://github.com/strawberry-graphql/strawberry/pull/2990/)


0.196.1 - 2023-07-26
--------------------

This release fixes an issue where annotations resolution for auto and lazy fields
using `Annotated` where not preserving the remaining arguments because of a
typo in the arguments filtering.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2983](https://github.com/strawberry-graphql/strawberry/pull/2983/)


0.196.0 - 2023-07-26
--------------------

This release adds support for union with a single member, they are
useful for future proofing your schema in cases you know a field
will be part of a union in future.

```python
import strawberry

from typing import Annotated


@strawberry.type
class Audio:
    duration: int


@strawberry.type
class Query:
    # note: Python's Union type doesn't support single members,
    # Union[Audio] is exactly the same as Audio, so we use
    # use Annotated and strawberry.union to tell Strawberry this is
    # a union with a single member
    latest_media: Annotated[Audio, strawberry.union("MediaItem")]


schema = strawberry.Schema(query=Query)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2982](https://github.com/strawberry-graphql/strawberry/pull/2982/)


0.195.3 - 2023-07-22
--------------------

This release no longer requires an upperbound pin for uvicorn, ensuring
compatibility with future versions of uvicorn without the need for updating
Strawberry.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2968](https://github.com/strawberry-graphql/strawberry/pull/2968/)


0.195.2 - 2023-07-15
--------------------

This release introduces a bug fix for relay connection where previously they wouldn't work without padding the `first` argument.

Contributed by [Alexander](https://github.com/devkral) via [PR #2938](https://github.com/strawberry-graphql/strawberry/pull/2938/)


0.195.1 - 2023-07-15
--------------------

This release fixes a bug where returning a generic type from a field
that was returning an interface would throw an error.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2955](https://github.com/strawberry-graphql/strawberry/pull/2955/)


0.195.0 - 2023-07-14
--------------------

Improve the time complexity of `strawberry.interface` using `resolve_type`.
Achieved time complexity is now O(1) with respect to the number of
implementations of an interface. Previously, the use of `is_type_of` resulted
in a worst-case performance of O(n).

**Before**:

```shell
---------------------------------------------------------------------------
Name (time in ms)                         Min                 Max
---------------------------------------------------------------------------
test_interface_performance[1]         18.0224 (1.0)       50.3003 (1.77)
test_interface_performance[16]        22.0060 (1.22)      28.4240 (1.0)
test_interface_performance[256]       69.1364 (3.84)      76.1349 (2.68)
test_interface_performance[4096]     219.6461 (12.19)    231.3732 (8.14)
---------------------------------------------------------------------------
```

**After**:

```shell
---------------------------------------------------------------------------
Name (time in ms)                        Min                Max
---------------------------------------------------------------------------
test_interface_performance[1]        14.3921 (1.0)      46.2064 (2.79)
test_interface_performance[16]       14.8669 (1.03)     16.5732 (1.0)
test_interface_performance[256]      15.8977 (1.10)     24.4618 (1.48)
test_interface_performance[4096]     18.7340 (1.30)     21.2899 (1.28)
---------------------------------------------------------------------------
```

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #1949](https://github.com/strawberry-graphql/strawberry/pull/1949/)


0.194.4 - 2023-07-08
--------------------

This release makes sure that `Schema.process_errors()` is called _once_ for every error
which happens with `graphql-transport-ws` operations.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2899](https://github.com/strawberry-graphql/strawberry/pull/2899/)


0.194.3 - 2023-07-08
--------------------

Added default argument to the typer Argument function, this adds
support for older versions of typer.

Contributed by [Jaime Coello de Portugal](https://github.com/jaimecp89) via [PR #2906](https://github.com/strawberry-graphql/strawberry/pull/2906/)


0.194.2 - 2023-07-08
--------------------

This release includes a performance improvement to `strawberry.lazy()` to allow relative module imports to be resolved faster.

Contributed by [Karim Alibhai](https://github.com/karimsa) via [PR #2926](https://github.com/strawberry-graphql/strawberry/pull/2926/)


0.194.1 - 2023-07-08
--------------------

This release adds a setter on `StrawberryAnnotation.annotation`, this fixes
an issue on Strawberry Django.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2932](https://github.com/strawberry-graphql/strawberry/pull/2932/)


0.194.0 - 2023-07-08
--------------------

Restore evaled type access in `StrawberryAnnotation`

Prior to Strawberry 192.2 the `annotation` attribute of `StrawberryAnnotation`
would return an evaluated type when possible due reserved argument parsing.
192.2 moved the responsibility of evaluating and caching results to the
`evaluate` method of `StrawberryAnnotation`. This introduced a regression when
using future annotations for any code implicitely relying on the `annotation`
attribute being an evaluated type.

To fix this regression and mimick pre-192.2 behavior, this release adds an
`annotation` property to `StrawberryAnnotation` that internally calls the
`evaluate` method. On success the evaluated type is returned. If a `NameError`
is raised due to an unresolvable annotation, the raw annotation is returned.

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #2925](https://github.com/strawberry-graphql/strawberry/pull/2925/)


0.193.1 - 2023-07-05
--------------------

This fixes a regression from 0.190.0 where changes to the
return type of a field done by Field Extensions would not
be taken in consideration by the schema.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2922](https://github.com/strawberry-graphql/strawberry/pull/2922/)


0.193.0 - 2023-07-04
--------------------

This release updates the API to listen to Django Channels to avoid race conditions
when confirming GraphQL subscriptions.

**Deprecations:**

This release contains a deprecation for the Channels integration. The `channel_listen`
method will be replaced with an async context manager that returns an awaitable
AsyncGenerator. This method is called `listen_to_channel`.

An example of migrating existing code is given below:

```py
# Existing code
@strawberry.type
class MyDataType:
    name: str


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def my_data_subscription(
        self, info: strawberry.Info, groups: list[str]
    ) -> AsyncGenerator[MyDataType | None, None]:
        yield None
        async for message in info.context["ws"].channel_listen(
            "my_data", groups=groups
        ):
            yield MyDataType(name=message["payload"])
```

```py
# New code
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def my_data_subscription(
        self, info: strawberry.Info, groups: list[str]
    ) -> AsyncGenerator[MyDataType | None, None]:
        async with info.context["ws"].listen_to_channel("my_data", groups=groups) as cm:
            yield None
            async for message in cm:
                yield MyDataType(name=message["payload"])
```

Contributed by [Moritz Ulmer](https://github.com/moritz89) via [PR #2856](https://github.com/strawberry-graphql/strawberry/pull/2856/)


0.192.2 - 2023-07-03
--------------------

This release fixes an issue related to using `typing.Annotated` in resolver
arguments following the declaration of a reserved argument such as
`strawberry.types.Info`.

Before this fix, the following would be converted incorrectly:

```python
from __future__ import annotations
import strawberry
import uuid
from typing_extensions import Annotated
from strawberry.types import Info


@strawberry.type
class Query:
    @strawberry.field
    def get_testing(
        self,
        info: strawberry.Info,
        id_: Annotated[uuid.UUID, strawberry.argument(name="id")],
    ) -> str | None:
        return None


schema = strawberry.Schema(query=Query)

print(schema)
```

Resulting in the schema:

```graphql
type Query {
  getTesting(id_: UUID!): String # ⬅️ see `id_`
}

scalar UUID
```

After this fix, the schema is converted correctly:

```graphql
type Query {
  getTesting(id: UUID!): String
}

scalar UUID
```

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #2901](https://github.com/strawberry-graphql/strawberry/pull/2901/)


0.192.1 - 2023-07-02
--------------------

Add specifications in FastAPI doc if query via GET is enabled

Contributed by [guillaumeLepape](https://github.com/guillaumeLepape) via [PR #2913](https://github.com/strawberry-graphql/strawberry/pull/2913/)


0.192.0 - 2023-06-28
--------------------

This release introduces a new command called `upgrade`, this command can be used
to run codemods on your codebase to upgrade to the latest version of Strawberry.

At the moment we only support upgrading unions to use the new syntax with
annotated, but in future we plan to add more commands to help with upgrading.

Here's how you can use the command to upgrade your codebase:

```shell
strawberry upgrade annotated-union .
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2886](https://github.com/strawberry-graphql/strawberry/pull/2886/)


0.191.0 - 2023-06-28
--------------------

This release adds support for declaring union types using `typing.Annotated`
instead of `strawberry.union(name, types=...)`.

Code using the old syntax will continue to work, but it will trigger a
deprecation warning. Using Annotated will improve type checking and IDE support
especially when using `pyright`.

Before:

```python
Animal = strawberry.union("Animal", (Cat, Dog))
```

After:

```python
from typing import Annotated, Union

Animal = Annotated[Union[Cat, Dog], strawberry.union("Animal")]
```

0.190.0 - 2023-06-27
--------------------

This release refactors the way we resolve field types to to make it
more robust, resolving some corner cases.

One case that should be fixed is when using specialized generics
with future annotations.

Contributed by [Alexander](https://github.com/devkral) via [PR #2868](https://github.com/strawberry-graphql/strawberry/pull/2868/)


0.189.3 - 2023-06-27
--------------------

This release removes some usage of deprecated functions from GraphQL-core.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2894](https://github.com/strawberry-graphql/strawberry/pull/2894/)


0.189.2 - 2023-06-27
--------------------

The `graphql-transport-ws` protocol allows for subscriptions to error during execution without terminating
the subscription.  Non-fatal errors produced by subscriptions now produce `Next` messages containing
an `ExecutionResult` with an `error` field and don't necessarily terminate the subscription.
This is in accordance to the behaviour of Apollo server.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2876](https://github.com/strawberry-graphql/strawberry/pull/2876/)


0.189.1 - 2023-06-25
--------------------

This release fixes a deprecation warning being triggered
by the relay integration.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2858](https://github.com/strawberry-graphql/strawberry/pull/2858/)


0.189.0 - 2023-06-22
--------------------

This release updates `create_type` to add support for all arguments
that `strawberry.type` supports. This includes: `description`, `extend`,
`directives`, `is_input` and `is_interface`.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2880](https://github.com/strawberry-graphql/strawberry/pull/2880/)


0.188.0 - 2023-06-22
--------------------

This release gives codegen clients the ability to inquire about the `__typename`
of a `GraphQLObjectType`.  This information can be used to automatically select
the proper type to hydrate when working with a union type in the response.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2875](https://github.com/strawberry-graphql/strawberry/pull/2875/)


0.187.5 - 2023-06-21
--------------------

This release fixes a regression when comparing a `StrawberryAnnotation`
instance with anything that is not also a `StrawberryAnnotation` instance,
which caused it to raise a `NotImplementedError`.

This reverts its behavior back to how it worked before, where it returns
`NotImplemented` instead, meaning that the comparison can be delegated to
the type being compared against or return `False` in case it doesn't define
an `__eq__` method.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2879](https://github.com/strawberry-graphql/strawberry/pull/2879/)


0.187.4 - 2023-06-21
--------------------

`graphql-transport-ws` handler now uses a single dict to manage active operations.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2699](https://github.com/strawberry-graphql/strawberry/pull/2699/)


0.187.3 - 2023-06-21
--------------------

This release fixes a typing regression on `StraberryContainer` subclasses
where type checkers would not allow non `WithStrawberryObjectDefinition` types
to be passed for its `of_type` argument (e.g. `StrawberryOptional(str)`)

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2878](https://github.com/strawberry-graphql/strawberry/pull/2878/)


0.187.2 - 2023-06-21
--------------------

This release removes `get_object_definition_strict` and instead
overloads `get_object_definition` to accept an extra `strct` keyword.

This is a new feature so it is unlikely to break anything.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2877](https://github.com/strawberry-graphql/strawberry/pull/2877/)


0.187.1 - 2023-06-21
--------------------

This release bumps the minimum requirement of
`typing-extensions` to 4.5

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2872](https://github.com/strawberry-graphql/strawberry/pull/2872/)


0.187.0 - 2023-06-20
--------------------

This release renames `_type_definition` to `__strawberry_definition__`. This doesn't change the public API of Strawberry, but if you were using `_type_definition` you can still access it, but it will be removed in future.

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #2836](https://github.com/strawberry-graphql/strawberry/pull/2836/)


0.186.3 - 2023-06-20
--------------------

This release adds resolve_async to NodeExtension to allow it to
be used together with other field async extensions/permissions.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2863](https://github.com/strawberry-graphql/strawberry/pull/2863/)


0.186.2 - 2023-06-19
--------------------

This release fixes an issue on StrawberryField.copy_with method
not copying its extensions and overwritten `_arguments`.

Also make sure that all lists/tuples in those types are copied as
new lists/tuples to avoid unexpected behavior.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2865](https://github.com/strawberry-graphql/strawberry/pull/2865/)


0.186.1 - 2023-06-16
--------------------

In this release, we pass the default values from the strawberry.Schema through to the codegen plugins.
The default python plugin now adds these default values to the objects it generates.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2860](https://github.com/strawberry-graphql/strawberry/pull/2860/)


0.186.0 - 2023-06-15
--------------------

This release removes more parts of the Mypy plugin, since they are
not needed anymore.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2852](https://github.com/strawberry-graphql/strawberry/pull/2852/)


0.185.2 - 2023-06-15
--------------------

This release fixes a bug causing a KeyError exception to be thrown during subscription cleanup.

Contributed by [rjwills28](https://github.com/rjwills28) via [PR #2794](https://github.com/strawberry-graphql/strawberry/pull/2794/)


0.185.1 - 2023-06-14
--------------------

Correct a type-hinting bug with `strawberry.directive`.
This may cause some consumers to have to remove a `# type: ignore` comment
or unnecessary `typing.cast` in order to get `mypy` to pass.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2847](https://github.com/strawberry-graphql/strawberry/pull/2847/)


0.185.0 - 2023-06-14
--------------------

This release removes our custom `__dataclass_transform__` decorator and replaces
it with typing-extension's one. It also removes parts of the mypy plugin, since
most of it is not needed anymore 🙌

This update requires typing_extensions>=4.1.0

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2227](https://github.com/strawberry-graphql/strawberry/pull/2227/)


0.184.1 - 2023-06-13
--------------------

This release migrates our CLI to typer, all commands
should work the same as before.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2569](https://github.com/strawberry-graphql/strawberry/pull/2569/)


0.184.0 - 2023-06-12
--------------------

This release improves the ﻿`relay.NodeID` annotation check by delaying it until after class initialization. This resolves issues with evaluating type annotations before they are fully defined and enables integrations to inject code for it in the type.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2838](https://github.com/strawberry-graphql/strawberry/pull/2838/)


0.183.8 - 2023-06-12
--------------------

This release fixes a bug in the codegen where `List` objects are currently emitted
as `Optional` objects.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2843](https://github.com/strawberry-graphql/strawberry/pull/2843/)


0.183.7 - 2023-06-12
--------------------

Refactor `ConnectionExtension` to copy arguments instead of extending them.
This should fix some issues with integrations which override `arguments`,
like the django one, where the inserted arguments were vanishing.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2839](https://github.com/strawberry-graphql/strawberry/pull/2839/)


0.183.6 - 2023-06-09
--------------------

This release fixes a bug where codegen would fail on mutations that have object arguments in the query.

Additionally, it does a topological sort of the types before passing it to the plugins to ensure that
dependent types are defined after their dependencies.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2831](https://github.com/strawberry-graphql/strawberry/pull/2831/)


0.183.5 - 2023-06-08
--------------------

This release fixes an issue where Strawberry would make copies
of types that were using specialized generics that were not
Strawerry types.

This issue combined with the use of lazy types was resulting
in duplicated type errors.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2824](https://github.com/strawberry-graphql/strawberry/pull/2824/)


0.183.4 - 2023-06-07
--------------------

This release fixes an issue for parsing lazy types using forward references
when they were enclosed in an `Optional[...]` type.

The following now should work properly:

```python
from __future__ import annotations

from typing import Optional, Annotated
import strawberry


@strawberry.type
class MyType:
    other_type: Optional[Annotated["OtherType", strawberry.lazy("some.module")]]
    # or like this
    other_type: Annotated["OtherType", strawberry.lazy("some.module")] | None
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2821](https://github.com/strawberry-graphql/strawberry/pull/2821/)


0.183.3 - 2023-06-07
--------------------

This release fixes a codegen bug.  Prior to this fix,
inline fragments would only include the last field defined
within its scope and all fields common with its siblings.

After this fix, all fields will be included in the
generated types.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2819](https://github.com/strawberry-graphql/strawberry/pull/2819/)


0.183.2 - 2023-06-07
--------------------

Fields with generics support directives.

Contributed by [A. Coady](https://github.com/coady) via [PR #2811](https://github.com/strawberry-graphql/strawberry/pull/2811/)


0.183.1 - 2023-06-06
--------------------

This release fixes an issue of the new relay integration adding an `id: GlobalID!`
argument on all objects that inherit from `relay.Node`. That should've only happened
for `Query` types.

Strawberry now will not force a `relay.Node` or any type that inherits it to be
inject the node extension which adds the argument and a resolver for it, meaning that
this code:

```python
import strawberry
from strawberry import relay


@strawberry.type
class Fruit(relay.Node):
    id: relay.NodeID[int]


@strawberry.type
class Query:
    node: relay.Node
    fruit: Fruit
```

Should now be written as:

```python
import strawberry
from strawberry import relay


@strawberry.type
class Fruit(relay.Node):
    id: relay.NodeID[int]


@strawberry.type
class Query:
    node: relay.Node = relay.node()  # <- note the "= relay.node()" here
    fruit: Fruit = relay.node()
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2814](https://github.com/strawberry-graphql/strawberry/pull/2814/)


0.183.0 - 2023-06-06
--------------------

This release adds a new field extension called `InputMutationExtension`, which makes
it easier to create mutations that receive a single input type called `input`,
while still being able to define the arguments of that input on the resolver itself.

The following example:

```python
import strawberry
from strawberry.field_extensions import InputMutationExtension


@strawberry.type
class Fruit:
    id: strawberry.ID
    name: str
    weight: float


@strawberry.type
class Mutation:
    @strawberry.mutation(extensions=[InputMutationExtension()])
    def update_fruit_weight(
        self,
        info: strawberry.Info,
        id: strawberry.ID,
        weight: Annotated[
            float,
            strawberry.argument(description="The fruit's new weight in grams"),
        ],
    ) -> Fruit:
        fruit = ...  # retrieve the fruit with the given ID
        fruit.weight = weight
        ...  # maybe save the fruit in the database
        return fruit
```

Would generate a schema like this:

```graphql
input UpdateFruitInput {
  id: ID!

  """
  The fruit's new weight in grams
  """
  weight: Float!
}

type Fruit {
  id: ID!
  name: String!
  weight: Float!
}

type Mutation {
  updateFruitWeight(input: UpdateFruitInput!): Fruit!
}
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2580](https://github.com/strawberry-graphql/strawberry/pull/2580/)


0.182.0 - 2023-06-06
--------------------

Initial relay spec implementation. For information on how to use
it, check out the docs in here: https://strawberry.rocks/docs/guides/relay

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2511](https://github.com/strawberry-graphql/strawberry/pull/2511/)


0.181.0 - 2023-06-06
--------------------

This release adds support for properly resolving lazy references
when using forward refs.

For example, this code should now work without any issues:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from some.module import OtherType


@strawberry.type
class MyType:
    @strawberry.field
    async def other_type(
        self,
    ) -> Annotated[OtherType, strawberry.lazy("some.module")]: ...
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2744](https://github.com/strawberry-graphql/strawberry/pull/2744/)


0.180.5 - 2023-06-02
--------------------

This release fixes a bug in fragment codegen to pick up type definitions from the proper place
in the schema.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2805](https://github.com/strawberry-graphql/strawberry/pull/2805/)


0.180.4 - 2023-06-02
--------------------

Custom codegen plugins will fail to write files if the plugin is trying to put the
file anywhere other than the root output directory (since the child directories do
not yet exist).  This change will create the child directory if necessary before
attempting to write the file.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2806](https://github.com/strawberry-graphql/strawberry/pull/2806/)


0.180.3 - 2023-06-02
--------------------

This release updates the built-in GraphiQL to the current latest version 2.4.7 and improves styling for the GraphiQL Explorer Plugin.

Contributed by [Kien Dang](https://github.com/kiendang) via [PR #2804](https://github.com/strawberry-graphql/strawberry/pull/2804/)


0.180.2 - 2023-06-02
--------------------

In this release codegen no longer chokes on queries that use a fragment.

There is one significant limitation at the present.  When a fragment is included via the spread operator in an object, it must be the only field present.  Attempts to include more fields will result in a ``ValueError``.

However, there are some real benefits.  When a fragment is included in multiple places in the query, only a single class will be made to represent that fragment:

```
fragment Point on Bar {
   id
   x
   y
}

query GetPoints {
  circlePoints {
    ...Point
  }
  squarePoints {
    ...Point
  }
}
```

Might generate the following types

```py
class Point:
    id: str
    x: float
    y: float


class GetPointsResult:
    circle_points: List[Point]
    square_points: List[Point]
```

The previous behavior would generate duplicate classes for for the `GetPointsCirclePoints` and `GetPointsSquarePoints` even though they are really identical classes.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2802](https://github.com/strawberry-graphql/strawberry/pull/2802/)


0.180.1 - 2023-06-01
--------------------

Make StrawberryAnnotation hashable, to make it compatible to newer versions of dacite.

Contributed by [Jaime Coello de Portugal](https://github.com/jaimecp89) via [PR #2790](https://github.com/strawberry-graphql/strawberry/pull/2790/)


0.180.0 - 2023-05-31
--------------------

This release updates the Django Channels integration so that it uses the same base
classes used by all other integrations.

**New features:**

The Django Channels integration supports two new features:

* Setting headers in a response
* File uploads via `multipart/form-data` POST requests

**Breaking changes:**

This release contains a breaking change for the Channels integration. The context
object is now a `dict` and it contains different keys depending on the connection
protocol:

1. HTTP: `request` and `response`. The `request` object contains the full
   request (including the body). Previously, `request` was the `GraphQLHTTPConsumer`
   instance of the current connection. The consumer is now available via
   `request.consumer`.
2. WebSockets: `request`, `ws` and `response`. `request` and `ws` are the same
   `GraphQLWSConsumer` instance of the current connection.

If you want to use a dataclass for the context object (like in previous releases),
you can still use them by overriding the `get_context` methods. See the Channels
integration documentation for an example.

Contributed by [Christian Dröge](https://github.com/cdroege) via [PR #2775](https://github.com/strawberry-graphql/strawberry/pull/2775/)


0.179.0 - 2023-05-31
--------------------

This PR allows passing metadata to Strawberry arguments.

Example:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(
        self,
        info,
        input: Annotated[str, strawberry.argument(metadata={"test": "foo"})],
    ) -> str:
        argument_definition = info.get_argument_definition("input")
        assert argument_definition.metadata["test"] == "foo"

        return f"Hi {input}"
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2755](https://github.com/strawberry-graphql/strawberry/pull/2755/)


0.178.3 - 2023-05-31
--------------------

In this release codegen no longer chokes on queries that have a `__typename` in them.
Python generated types will not have the `__typename` included in the fields.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2797](https://github.com/strawberry-graphql/strawberry/pull/2797/)


0.178.2 - 2023-05-31
--------------------

Prevent AssertionError when using `strawberry codegen` on a query file that contains a mutation.

Contributed by [Matt Gilson](https://github.com/mgilson) via [PR #2795](https://github.com/strawberry-graphql/strawberry/pull/2795/)


0.178.1 - 2023-05-30
--------------------

This release fixes a bug in experimental.pydantic whereby `Optional` type annotations weren't exactly aligned between strawberry type and pydantic model.

Previously this would have caused the series field to be non-nullable in graphql.
```python
from typing import Optional
from pydantic import BaseModel, Field
import strawberry


class VehicleModel(BaseModel):
    series: Optional[str] = Field(default="")


@strawberry.experimental.pydantic.type(model=VehicleModel, all_fields=True)
class VehicleModelType:
    pass
```

Contributed by [Nick Butlin](https://github.com/nicholasbutlin) via [PR #2782](https://github.com/strawberry-graphql/strawberry/pull/2782/)


0.178.0 - 2023-05-22
--------------------

This release introduces the new `should_ignore` argument to the `QueryDepthLimiter` extension that provides
a more general and more verbose way of specifying the rules by which a query's depth should be limited.

The `should_ignore` argument should be a function that accepts a single argument of type `IgnoreContext`.
The `IgnoreContext` class has the following attributes:
- `field_name` of type `str`: the name of the field to be compared against
- `field_args` of type `strawberry.extensions.query_depth_limiter.FieldArgumentsType`: the arguments of the field to be compared against
- `query` of type `graphql.language.Node`: the query string
- `context` of type `graphql.validation.ValidationContext`: the context passed to the query
and returns `True` if the field should be ignored and `False` otherwise.
This argument is injected, regardless of name, by the `QueryDepthLimiter` class and should not be passed by the user.

Instead, the user should write business logic to determine whether a field should be ignored or not by
the attributes of the `IgnoreContext` class.

For example, the following query:
```python
"""
    query {
      matt: user(name: "matt") {
        email
      }
      andy: user(name: "andy") {
        email
        address {
          city
        }
        pets {
          name
          owner {
            name
          }
        }
      }
    }
"""
```
can have its depth limited by the following `should_ignore`:
```python
from strawberry.extensions import IgnoreContext


def should_ignore(ignore: IgnoreContext):
    return ignore.field_args.get("name") == "matt"


query_depth_limiter = QueryDepthLimiter(should_ignore=should_ignore)
```
so that it *effectively* becomes:
```python
"""
    query {
      andy: user(name: "andy") {
        email
        pets {
          name
          owner {
            name
          }
        }
      }
    }
"""
```

Contributed by [Tommy Smith](https://github.com/tsmith023) via [PR #2505](https://github.com/strawberry-graphql/strawberry/pull/2505/)


0.177.3 - 2023-05-19
--------------------

This release adds a method on the DatadogTracingExtension class called `create_span` that can be overridden to create a custom span or add additional tags to the span.

```python
from ddtrace import Span

from strawberry.extensions import LifecycleStep
from strawberry.extensions.tracing import DatadogTracingExtension


class DataDogExtension(DatadogTracingExtension):
    def create_span(
        self,
        lifecycle_step: LifecycleStep,
        name: str,
        **kwargs,
    ) -> Span:
        span = super().create_span(lifecycle_step, name, **kwargs)
        if lifecycle_step == LifeCycleStep.OPERATION:
            span.set_tag("graphql.query", self.execution_context.query)
        return span
```

Contributed by [Ronald Williams](https://github.com/ronaldnwilliams) via [PR #2773](https://github.com/strawberry-graphql/strawberry/pull/2773/)


0.177.2 - 2023-05-18
--------------------

This release fixes an issue with optional scalars using the `or`
notation with forward references on python 3.10.

The following code would previously raise `TypeError` on python 3.10:

```python
from __future__ import annotations

import strawberry
from strawberry.scalars import JSON


@strawberry.type
class SomeType:
    an_optional_json: JSON | None
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2774](https://github.com/strawberry-graphql/strawberry/pull/2774/)


0.177.1 - 2023-05-09
--------------------

This release adds support for using `enum_value` with `IntEnum`s, like this:

```python
import strawberry

from enum import IntEnum


@strawberry.enum
class Color(IntEnum):
    OTHER = strawberry.enum_value(
        -1, description="Other: The color is not red, blue, or green."
    )
    RED = strawberry.enum_value(0, description="Red: The color red.")
    BLUE = strawberry.enum_value(1, description="Blue: The color blue.")
    GREEN = strawberry.enum_value(2, description="Green: The color green.")
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2761](https://github.com/strawberry-graphql/strawberry/pull/2761/)


0.177.0 - 2023-05-07
--------------------

This release adds a SentryTracingExtension that you can use to automatically add
tracing information to your GraphQL queries.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2495](https://github.com/strawberry-graphql/strawberry/pull/2495/)


0.176.4 - 2023-05-07
--------------------

This release adds support for custom classes inside the OpenTelemetry integration.
With this, we shouldn't see errors like this anymore:

```Invalid type dict for attribute 'graphql.param.paginator' value. Expected one of ['bool', 'str', 'bytes', 'int', 'float'] or a sequence of those types.```

Contributed by [Budida Abhinav Ramana](https://github.com/abhinavramana) via [PR #2753](https://github.com/strawberry-graphql/strawberry/pull/2753/)


0.176.3 - 2023-05-03
--------------------

Add `get_argument_definition` helper function on the Info object to get
a StrawberryArgument definition by argument name from inside a resolver or
Field Extension.

Example:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def field(
        self,
        info,
        my_input: Annotated[
            str,
            strawberry.argument(description="Some description"),
        ],
    ) -> str:
        my_input_def = info.get_argument_definition("my_input")
        assert my_input_def.type is str
        assert my_input_def.description == "Some description"

        return my_input
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2732](https://github.com/strawberry-graphql/strawberry/pull/2732/)


0.176.2 - 2023-05-02
--------------------

This release adds more type hints to internal APIs and public APIs.

Contributed by [Alex Auritt](https://github.com/alexauritt) via [PR #2568](https://github.com/strawberry-graphql/strawberry/pull/2568/)


0.176.1 - 2023-05-02
--------------------

This release improves the `graphql-transport-ws` implementation by starting the sub-protocol timeout only when the connection handshake is completed.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2703](https://github.com/strawberry-graphql/strawberry/pull/2703/)


0.176.0 - 2023-05-01
--------------------

This release parses the input arguments to a field earlier so that Field
Extensions recieve instances of Input types rather than plain dictionaries.

Example:

```python
import strawberry
from strawberry.extensions import FieldExtension


@strawberry.input
class MyInput:
    foo: str


class MyFieldExtension(FieldExtension):
    def resolve(
        self, next_: Callable[..., Any], source: Any, info: strawberry.Info, **kwargs
    ):
        # kwargs["my_input"] is instance of MyInput
        ...


@strawberry.type
class Query:
    @strawberry.field
    def field(self, my_input: MyInput) -> str:
        return "hi"
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2731](https://github.com/strawberry-graphql/strawberry/pull/2731/)


0.175.1 - 2023-04-30
--------------------

This release adds a missing parameter to `get_context`
when using subscriptions with ASGI.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2739](https://github.com/strawberry-graphql/strawberry/pull/2739/)


0.175.0 - 2023-04-29
--------------------

Do not display graphiql view in fastapi doc if graphiql parameter is deactivated

Contributed by [yak-toto](https://github.com/yak-toto) via [PR #2736](https://github.com/strawberry-graphql/strawberry/pull/2736/)


0.174.0 - 2023-04-25
--------------------

This PR adds a MaxTokensLimiter extension which limits the number of tokens in a GraphQL document.

## Usage example:

```python
import strawberry
from strawberry.extensions import MaxTokensLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        MaxTokensLimiter(max_token_count=1000),
    ],
)
```

Contributed by [reka](https://github.com/reka) via [PR #2729](https://github.com/strawberry-graphql/strawberry/pull/2729/)


0.173.1 - 2023-04-25
--------------------

This release bumps the version of typing_extensions to >= `4.0.0` to fix the
error: `"cannot import Self from typing_extensions"`.

Contributed by [Tien Truong](https://github.com/tienman) via [PR #2704](https://github.com/strawberry-graphql/strawberry/pull/2704/)


0.173.0 - 2023-04-25
--------------------

This releases adds an extension for [PyInstrument](https://github.com/joerick/pyinstrument). It allows to instrument your server and find slow code paths.

You can use it like this:

```python
import strawberry
from strawberry.extensions import pyinstrument

schema = strawberry.Schema(
    Query,
    extensions=[
        pyinstrument.PyInstrument(report_path="pyinstrument.html"),
    ],
)
```

Contributed by [Peyton Duncan](https://github.com/Helithumper) via [PR #2727](https://github.com/strawberry-graphql/strawberry/pull/2727/)


0.172.0 - 2023-04-24
--------------------

This PR adds a MaxAliasesLimiter extension which limits the number of aliases in a GraphQL document.

## Usage example:

```python
import strawberry
from strawberry.extensions import MaxAliasesLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        MaxAliasesLimiter(max_alias_count=15),
    ],
)
```

Contributed by [reka](https://github.com/reka) via [PR #2726](https://github.com/strawberry-graphql/strawberry/pull/2726/)


0.171.3 - 2023-04-21
--------------------

This release adds missing annotations in class methods, improving
our type coverage.

Contributed by [Kai Benevento](https://github.com/benesgarage) via [PR #2721](https://github.com/strawberry-graphql/strawberry/pull/2721/)


0.171.2 - 2023-04-21
--------------------

`graphql_transport_ws`: Cancelling a subscription no longer blocks the connection
while any subscription finalizers run.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2718](https://github.com/strawberry-graphql/strawberry/pull/2718/)


0.171.1 - 2023-04-07
--------------------

This release fix the return value of enums when using a custom
name converter for them.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2696](https://github.com/strawberry-graphql/strawberry/pull/2696/)


0.171.0 - 2023-04-06
--------------------

This release adds support for Mypy 1.2.0

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2693](https://github.com/strawberry-graphql/strawberry/pull/2693/)


0.170.0 - 2023-04-06
--------------------

This release add support for converting the enum value names
from `NameConverter`. It looks like this:


```python
from enum import Enum

import strawberry
from strawberry.enum import EnumDefinition, EnumValue
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.name_converter import NameConverter


class EnumNameConverter(NameConverter):
    def from_enum_value(self, enum: EnumDefinition, enum_value: EnumValue) -> str:
        return f"{super().from_enum_value(enum, enum_value)}_enum_value"


@strawberry.enum
class MyEnum(Enum):
    A = "a"
    B = "b"


@strawberry.type
class Query:
    a_enum: MyEnum


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(name_converter=EnumNameConverter()),
)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2690](https://github.com/strawberry-graphql/strawberry/pull/2690/)


0.169.0 - 2023-04-05
--------------------

This release updates all\* the HTTP integration to use the same base class,
which makes it easier to maintain and extend them in future releases.

While this doesn't provide any new features (other than settings headers in
Chalice and Sanic), it does make it easier to extend the HTTP integrations in
the future. So, expect some new features in the next releases!

**New features:**

Now both Chalice and Sanic integrations support setting headers in the response.
Bringing them to the same level as the other HTTP integrations.

**Breaking changes:**

Unfortunately, this release does contain some breaking changes, but they are
minimal and should be quick to fix.

1. Flask `get_root_value` and `get_context` now receive the request
2. Sanic `get_root_value` now receives the request and it is async

\* The only exception is the channels http integration, which will be updated in
a future release.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2681](https://github.com/strawberry-graphql/strawberry/pull/2681/)


0.168.2 - 2023-04-03
--------------------

Fixes type hint for StrawberryTypeFromPydantic._pydantic_type to be a Type instead of an instance of the Pydantic model.
As it is a private API, we still highly discourage using it, but it's now typed correctly.

```python
from pydantic import BaseModel
from typing import Type, List

import strawberry
from strawberry.experimental.pydantic.conversion_types import StrawberryTypeFromPydantic


class User(BaseModel):
    name: str

    @staticmethod
    def foo() -> List[str]:
        return ["Patrick", "Pietro", "Pablo"]


@strawberry.experimental.pydantic.type(model=User, all_fields=True)
class UserType:
    @strawberry.field
    def foo(self: StrawberryTypeFromPydantic[User]) -> List[str]:
        # This is now inferred correctly as Type[User] instead of User
        # We still highly discourage using this private API, but it's
        # now typed correctly
        pydantic_type: Type[User] = self._pydantic_type
        return pydantic_type.foo()


def get_users() -> UserType:
    user: User = User(name="Patrick")
    return UserType.from_pydantic(user)


@strawberry.type
class Query:
    user: UserType = strawberry.field(resolver=get_users)


schema = strawberry.Schema(query=Query)
```

Contributed by [James Chua](https://github.com/thejaminator) via [PR #2683](https://github.com/strawberry-graphql/strawberry/pull/2683/)


0.168.1 - 2023-03-26
--------------------

This releases adds a new `extra` group for Starlite, preventing it from being
installed by default.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2664](https://github.com/strawberry-graphql/strawberry/pull/2664/)


0.168.0 - 2023-03-26
--------------------

This release adds support for [starlite](https://starliteproject.dev/).

```python
import strawberry
from starlite import Request, Starlite
from strawberry.starlite import make_graphql_controller
from strawberry.types.info import Info


def custom_context_getter(request: Request):
    return {"custom": "context"}


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info: strawberry.Info[object, None]) -> str:
        return info.context["custom"]


schema = strawberry.Schema(Query)


GraphQLController = make_graphql_controller(
    schema,
    path="/graphql",
    context_getter=custom_context_getter,
)

app = Starlite(
    route_handlers=[GraphQLController],
)
```

Contributed by [Matthieu MN](https://github.com/gazorby) via [PR #2391](https://github.com/strawberry-graphql/strawberry/pull/2391/)


0.167.1 - 2023-03-26
--------------------

This release fixes and issue where you'd get a warning
about using Apollo Federation directives even when using
`strawberry.federation.Schema`.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2661](https://github.com/strawberry-graphql/strawberry/pull/2661/)


0.167.0 - 2023-03-25
--------------------

This releases adds more type annotations for public functions and methods.

No new changes have been added to the API.

Contributed by [Jad Haddad](https://github.com/JadHADDAD92) via [PR #2627](https://github.com/strawberry-graphql/strawberry/pull/2627/)


0.166.0 - 2023-03-25
--------------------

This release adds a warning when using `@strawberry.federation.type`
but not using `strawberry.federation.Schema`

Contributed by [Rubens O Leão](https://github.com/rubensoleao) via [PR #2572](https://github.com/strawberry-graphql/strawberry/pull/2572/)


0.165.1 - 2023-03-21
--------------------

Updates the `MaskErrors` extension to the new extension API, which was missed previously.

Contributed by [Nikolai Maas](https://github.com/N-Maas) via [PR #2655](https://github.com/strawberry-graphql/strawberry/pull/2655/)


0.165.0 - 2023-03-18
--------------------

Add full support for forward references, specially when using
`from __future__ import annotations`.

Before the following would fail on python versions older than 3.10:

```python
from __future__ import annotations

import strawberry


@strawberry.type
class Query:
    foo: str | None
```

Also, this would fail in any python versions:

```python
from __future__ import annotations

from typing import Annotated

import strawberry


@strawberry.type
class Query:
    foo: Annotated[str, "some annotation"]
```

Now both of these cases are supported.
Please open an issue if you find any edge cases that are still not supported.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2592](https://github.com/strawberry-graphql/strawberry/pull/2592/)


0.164.1 - 2023-03-18
--------------------

Fix interface duplication leading to schema compilation error in multiple
inheritance scenarios (i.e. "Diamond Problem" inheritance)

Thank you @mzhu22 for the thorough bug report!

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #2647](https://github.com/strawberry-graphql/strawberry/pull/2647/)


0.164.0 - 2023-03-14
--------------------

This release introduces a breaking change to make pydantic default behavior consistent with normal strawberry types.
This changes the schema generated for pydantic types, that are required, and have default values.
Previously pydantic type with a default, would get converted to a strawberry type that is not required.
This is now fixed, and the schema will now correctly show the type as required.

```python
import pydantic
import strawberry


class UserPydantic(pydantic.BaseModel):
    name: str = "James"


@strawberry.experimental.pydantic.type(UserPydantic, all_fields=True)
class User: ...


@strawberry.type
class Query:
    a: User = strawberry.field()

    @strawberry.field
    def a(self) -> User:
        return User()
```
The schema is now
```
type Query {
  a: User!
}

type User {
  name: String! // String! rather than String previously
}
```

Contributed by [James Chua](https://github.com/thejaminator) via [PR #2623](https://github.com/strawberry-graphql/strawberry/pull/2623/)


0.163.2 - 2023-03-14
--------------------

This release covers an edge case where the following would not give a nice error.
```python
some_field: "Union[list[str], SomeType]]"
```
Fixes [#2591](https://github.com/strawberry-graphql/strawberry/issues/2591)

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #2593](https://github.com/strawberry-graphql/strawberry/pull/2593/)


0.163.1 - 2023-03-14
--------------------

Provide close reason to ASGI websocket as specified by ASGI 2.3

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2639](https://github.com/strawberry-graphql/strawberry/pull/2639/)


0.163.0 - 2023-03-13
--------------------

This release adds support for list arguments in operation directives.

The following is now supported:

```python
@strawberry.directive(locations=[DirectiveLocation.FIELD])
def append_names(
    value: DirectiveValue[str], names: List[str]
):  # note the usage of List here
    return f"{value} {', '.join(names)}"
```

Contributed by [chenyijian](https://github.com/hot123s) via [PR #2632](https://github.com/strawberry-graphql/strawberry/pull/2632/)


0.162.0 - 2023-03-10
--------------------

Adds support for a custom field using the approach specified in issue [#2168](abc).
Field Extensions may be used to change the way how fields work and what they return.
Use cases might include pagination, permissions or other behavior modifications.

```python
from strawberry.extensions import FieldExtension


class UpperCaseExtension(FieldExtension):
    async def resolve_async(
        self,
        next: Callable[..., Awaitable[Any]],
        source: Any,
        info: strawberry.Info,
        **kwargs
    ):
        result = await next(source, info, **kwargs)
        return str(result).upper()


@strawberry.type
class Query:
    @strawberry.field(extensions=[UpperCaseExtension()])
    async def string(self) -> str:
        return "This is a test!!"
```

```graphql
query {
    string
}
```

```json
{
  "string": "THIS IS A TEST!!"
}
```

Contributed by [Erik Wrede](https://github.com/erikwrede) via [PR #2567](https://github.com/strawberry-graphql/strawberry/pull/2567/)


0.161.1 - 2023-03-09
--------------------

Ensure that no other messages follow a "complete" or "error" message
for an operation in the graphql-transport-ws protocol.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2600](https://github.com/strawberry-graphql/strawberry/pull/2600/)


0.161.0 - 2023-03-08
--------------------

Calling `ChannelsConsumer.channel_listen` multiple times will now pass
along the messages being listened for to multiple callers, rather than
only one of the callers, which was the old behaviour.

This resolves an issue where creating multiple GraphQL subscriptions
using a single websocket connection could result in only one of those
subscriptions (in a non-deterministic order) being triggered if they
are listening for channel layer messages of the same type.

Contributed by [James Thorniley](https://github.com/jthorniley) via [PR #2525](https://github.com/strawberry-graphql/strawberry/pull/2525/)


0.160.0 - 2023-03-08
--------------------

Rename `Extension` to `SchemaExtension` to pave the way for FieldExtensions.
Importing `Extension` from `strawberry.extensions` will now raise a deprecation
warning.

Before:

```python
from strawberry.extensions import Extension
```

After:

```python
from strawberry.extensions import SchemaExtension
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2574](https://github.com/strawberry-graphql/strawberry/pull/2574/)


0.159.1 - 2023-03-07
--------------------

This releases adds support for Mypy 1.1.1

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2616](https://github.com/strawberry-graphql/strawberry/pull/2616/)


0.159.0 - 2023-02-22
--------------------

This release changes how extension hooks are defined. The new style hooks are
more flexible and allow to run code before and after the execution.

The old style hooks are still supported but will be removed in future releases.

**Before:**

```python
def on_executing_start(self):  # Called before the execution start
    ...


def on_executing_end(self):  # Called after the execution ends
    ...
```

**After**

```python
def on_execute(self):
    #  This part is called before the execution start
    yield
    #  This part is called after the execution ends
```

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #2428](https://github.com/strawberry-graphql/strawberry/pull/2428/)


0.158.2 - 2023-02-21
--------------------

Add a type annotation to `strawberry.fastapi.BaseContext`'s `__init__` method so that
it can be used without `mypy` raising an error.

Contributed by [Martin Winkel](https://github.com/SaturnFromTitan) via [PR #2581](https://github.com/strawberry-graphql/strawberry/pull/2581/)


0.158.1 - 2023-02-19
--------------------

Version 1.5.10 of GraphiQL disabled introspection for deprecated
arguments because it wasn't supported by all GraphQL server versions.
This PR enables it so that deprecated arguments show up again in
GraphiQL.

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2575](https://github.com/strawberry-graphql/strawberry/pull/2575/)


0.158.0 - 2023-02-18
--------------------

Throw proper exceptions when Unions are created with invalid types

Previously, using Lazy types inside of Unions would raise unexpected, unhelpful errors.

Contributed by [ignormies](https://github.com/BryceBeagle) via [PR #2540](https://github.com/strawberry-graphql/strawberry/pull/2540/)


0.157.0 - 2023-02-18
--------------------

This releases adds support for Apollo Federation 2.1, 2.2 and 2.3.

This includes support for `@composeDirective` and `@interfaceObject`,
we expose directives for both, but we also have shortcuts, for example
to use `@composeDirective` with a custom schema directive, you can do
the following:

```python
@strawberry.federation.schema_directive(
    locations=[Location.OBJECT], name="cacheControl", compose=True
)
class CacheControl:
    max_age: int
```

The `compose=True` makes so that this directive is included in the supergraph
schema.

For `@interfaceObject` we introduced a new `@strawberry.federation.interface_object`
decorator. This works like `@strawberry.federation.type`, but it adds, the appropriate
directive, for example:

```python
@strawberry.federation.interface_object(keys=["id"])
class SomeInterface:
    id: strawberry.ID
```

generates the following type:

```graphql
type SomeInterface @key(fields: "id") @interfaceObject {
  id: ID!
}
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2549](https://github.com/strawberry-graphql/strawberry/pull/2549/)


0.156.4 - 2023-02-13
--------------------

This release fixes a regression introduce in version 0.156.2 that
would make Mypy throw an error in the following code:

```python
import strawberry


@strawberry.type
class Author:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    async def get_authors(self) -> list[Author]:
        return [Author(name="Michael Crichton")]
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2535](https://github.com/strawberry-graphql/strawberry/pull/2535/)


0.156.3 - 2023-02-10
--------------------

This release adds support for Mypy 1.0

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2516](https://github.com/strawberry-graphql/strawberry/pull/2516/)


0.156.2 - 2023-02-09
--------------------

This release updates the typing for the resolver argument in
`strawberry.field`i to support async resolvers.
This means that now you won't get any type
error from Pyright when using async resolver, like the following example:

```python
import strawberry


async def get_user_age() -> int:
    return 0


@strawberry.type
class User:
    name: str
    age: int = strawberry.field(resolver=get_user_age)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2528](https://github.com/strawberry-graphql/strawberry/pull/2528/)


0.156.1 - 2023-02-09
--------------------

Add `GraphQLWebsocketCommunicator` for testing websockets on channels.
i.e:

```python
import pytest
from strawberry.channels.testing import GraphQLWebsocketCommunicator
from myapp.asgi import application


@pytest.fixture
async def gql_communicator():
    async with GraphQLWebsocketCommunicator(
        application=application, path="/graphql"
    ) as client:
        yield client


async def test_subscribe_echo(gql_communicator):
    async for res in gql_communicator.subscribe(
        query='subscription { echo(message: "Hi") }'
    ):
        assert res.data == {"echo": "Hi"}
```

Contributed by [ניר](https://github.com/nrbnlulu) via [PR #2458](https://github.com/strawberry-graphql/strawberry/pull/2458/)


0.156.0 - 2023-02-08
--------------------

This release adds support for specialized generic types.
Before, the following code would give an error, saying that `T` was not
provided to the generic type:

```python
@strawberry.type
class Foo(Generic[T]):
    some_var: T


@strawberry.type
class IntFoo(Foo[int]): ...


@strawberry.type
class Query:
    int_foo: IntFoo
```

Also, because the type is already specialized, `Int` won't get inserted to its name,
meaning it will be exported to the schema with a type name of `IntFoo` and not
`IntIntFoo`.

For example, this query:

```python
@strawberry.type
class Query:
    int_foo: IntFoo
    str_foo: Foo[str]
```

Will generate a schema like this:

```graphql
type IntFoo {
  someVar: Int!
}

type StrFoo {
  someVar: String!
}

type Query {
  intFoo: IntFoo!
  strfoo: StrFoo!
}
```

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2517](https://github.com/strawberry-graphql/strawberry/pull/2517/)


0.155.4 - 2023-02-06
--------------------

Fix file not found error when exporting schema with lazy types from CLI #2469

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #2512](https://github.com/strawberry-graphql/strawberry/pull/2512/)


0.155.3 - 2023-02-01
--------------------

Fix missing custom `resolve_reference` for using pydantic with federation

i.e:

```python
import typing
from pydantic import BaseModel
import strawberry
from strawberry.federation.schema_directives import Key


class ProductInDb(BaseModel):
    upc: str
    name: str


@strawberry.experimental.pydantic.type(
    model=ProductInDb, directives=[Key(fields="upc", resolvable=True)]
)
class Product:
    upc: str
    name: str

    @classmethod
    def resolve_reference(cls, upc):
        return Product(upc=upc, name="")
```

Contributed by [filwaline](https://github.com/filwaline) via [PR #2503](https://github.com/strawberry-graphql/strawberry/pull/2503/)


0.155.2 - 2023-01-25
--------------------

This release fixes a bug in subscriptions using the graphql-transport-ws protocol
where the conversion of the NextMessage object to a dictionary took an unnecessary
amount of time leading to an increase in CPU usage.

Contributed by [rjwills28](https://github.com/rjwills28) via [PR #2481](https://github.com/strawberry-graphql/strawberry/pull/2481/)


0.155.1 - 2023-01-24
--------------------

A link to the changelog has been added to the package metadata, so it shows up on PyPI.

Contributed by [Tom Most](https://github.com/twm) via [PR #2490](https://github.com/strawberry-graphql/strawberry/pull/2490/)


0.155.0 - 2023-01-23
--------------------

This release adds a new utility function to convert a Strawberry object to a
dictionary.

You can use `strawberry.asdict(...)` function to convert a Strawberry object to
a dictionary:

```python
@strawberry.type
class User:
    name: str
    age: int


# should be {"name": "Lorem", "age": 25}
user_dict = strawberry.asdict(User(name="Lorem", age=25))
```

> Note: This function uses the `dataclasses.asdict` function under the hood, so
> you can safely replace `dataclasses.asdict` with `strawberry.asdict` in your
> code. This will make it easier to update your code to newer versions of
> Strawberry if we decide to change the implementation.

Contributed by [Haze Lee](https://github.com/Hazealign) via [PR #2417](https://github.com/strawberry-graphql/strawberry/pull/2417/)


0.154.1 - 2023-01-17
--------------------

Fix `DuplicatedTypeName` exception being raised on generics declared using
`strawberry.lazy`. Previously the following would raise:

```python
# issue_2397.py
from typing import Annotated, Generic, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.type
class Item:
    name: str


@strawberry.type
class Edge(Generic[T]):
    node: T


@strawberry.type
class Query:
    edges_normal: Edge[Item]
    edges_lazy: Edge[Annotated["Item", strawberry.lazy("issue_2397")]]


if __name__ == "__main__":
    schema = strawberry.Schema(query=Query)
```

Contributed by [pre-commit-ci](https://github.com/pre-commit-ci) via [PR #2462](https://github.com/strawberry-graphql/strawberry/pull/2462/)


0.154.0 - 2023-01-13
--------------------

Support constrained float field types in Pydantic models.

i.e.

```python
import pydantic


class Model(pydantic.BaseModel):
    field: pydantic.confloat(le=100.0)
    equivalent_field: float = pydantic.Field(le=100.0)
```

Contributed by [Etienne Wodey](https://github.com/airwoodix) via [PR #2455](https://github.com/strawberry-graphql/strawberry/pull/2455/)


0.153.0 - 2023-01-13
--------------------

This change allows clients to define connectionParams when making Subscription requests similar to the way [Apollo-Server](https://www.apollographql.com/docs/apollo-server/data/subscriptions/#operation-context) does it.

With [Apollo-Client (React)](https://www.apollographql.com/docs/react/data/subscriptions/#5-authenticate-over-websocket-optional) as an example, define a Websocket Link:
```
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';

const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:4000/subscriptions',
  connectionParams: {
    authToken: user.authToken,
  },
}));
```
and the JSON passed to `connectionParams` here will appear within Strawberry's context as the `connection_params` attribute when accessing `info.context` within a Subscription resolver.

Contributed by [Tommy Smith](https://github.com/tsmith023) via [PR #2380](https://github.com/strawberry-graphql/strawberry/pull/2380/)


0.152.0 - 2023-01-10
--------------------

This release adds support for updating (or adding) the query document inside an
extension's `on_request_start` method.

This can be useful for implementing persisted queries. The old behavior of
returning a 400 error if no query is present in the request is still supported.

Example usage:

```python
from strawberry.extensions import Extension


def get_doc_id(request) -> str:
    """Implement this to get the document ID using your framework's request object"""
    ...


def load_persisted_query(doc_id: str) -> str:
    """Implement this load a query by document ID. For example, from a database."""
    ...


class PersistedQuery(Extension):
    def on_request_start(self):
        request = self.execution_context.context.request

        doc_id = get_doc_id(request)

        self.execution_context.query = load_persisted_query(doc_id)
```

Contributed by [James Thorniley](https://github.com/jthorniley) via [PR #2431](https://github.com/strawberry-graphql/strawberry/pull/2431/)


0.151.3 - 2023-01-09
--------------------

This release adds support for FastAPI 0.89.0

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2440](https://github.com/strawberry-graphql/strawberry/pull/2440/)


0.151.2 - 2022-12-23
--------------------

This release fixes `@strawberry.experimental.pydantic.type` and adds support for the metadata attribute on fields.

Example:
```python
@strawberry.experimental.pydantic.type(model=User)
class UserType:
    private: strawberry.auto = strawberry.field(metadata={"admin_only": True})
    public: strawberry.auto
```

Contributed by [Huy Z](https://github.com/huyz) via [PR #2415](https://github.com/strawberry-graphql/strawberry/pull/2415/)


0.151.1 - 2022-12-20
--------------------

This release fixes an issue that prevented using generic
that had a field of type enum. The following works now:

```python
@strawberry.enum
class EstimatedValueEnum(Enum):
    test = "test"
    testtest = "testtest"


@strawberry.type
class EstimatedValue(Generic[T]):
    value: T
    type: EstimatedValueEnum


@strawberry.type
class Query:
    @strawberry.field
    def estimated_value(self) -> Optional[EstimatedValue[int]]:
        return EstimatedValue(value=1, type=EstimatedValueEnum.test)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2411](https://github.com/strawberry-graphql/strawberry/pull/2411/)


0.151.0 - 2022-12-13
--------------------

This PR adds a new `graphql_type` parameter to strawberry.field that allows you
to explicitly set the field type. This parameter will take preference over the
resolver return type and the class field type.

For example:

```python
@strawberry.type
class Query:
    a: float = strawberry.field(graphql_type=str)
    b = strawberry.field(graphql_type=int)

    @strawberry.field(graphql_type=float)
    def c(self) -> str:
        return "3.4"


schema = strawberry.Schema(Query)

str(
    schema
) == """
  type Query {
    a: String!
    b: Int!
    c: Float!
  }
"""
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2313](https://github.com/strawberry-graphql/strawberry/pull/2313/)


0.150.1 - 2022-12-13
--------------------

Fixed field resolvers with nested generic return types
(e.g. `list`, `Optional`, `Union` etc) raising TypeErrors.
This means resolver factory methods can now be correctly type hinted.

For example the below would previously error unless you ommited all the
type hints on `resolver_factory` and `actual_resolver` functions.
```python
from typing import Callable, Optional, Type, TypeVar

import strawberry


@strawberry.type
class Cat:
    name: str


T = TypeVar("T")


def resolver_factory(type_: Type[T]) -> Callable[[], Optional[T]]:
    def actual_resolver() -> Optional[T]:
        # load rows from database and cast to type etc
        ...

    return actual_resolver


@strawberry.type
class Query:
    cat: Cat = strawberry.field(resolver_factory(Cat))


schema = strawberry.Schema(query=Query)
```

Contributed by [Tim OSullivan](https://github.com/invokermain) via [PR #1900](https://github.com/strawberry-graphql/strawberry/pull/1900/)


0.150.0 - 2022-12-13
--------------------

This release implements the ability to use custom caching for dataloaders.
It also allows to provide a `cache_key_fn` to the dataloader. This function
is used to generate the cache key for the dataloader. This is useful when
you want to use a custom hashing function for the cache key.

Contributed by [Aman Choudhary](https://github.com/Techno-Tut) via [PR #2394](https://github.com/strawberry-graphql/strawberry/pull/2394/)


0.149.2 - 2022-12-09
--------------------

This release fixes support for generics in arguments, see the following example:

 ```python
 T = TypeVar("T")


 @strawberry.type
 class Node(Generic[T]):
     @strawberry.field
     def data(self, arg: T) -> T:  # `arg` is also generic
         return arg
 ```

Contributed by [A. Coady](https://github.com/coady) via [PR #2316](https://github.com/strawberry-graphql/strawberry/pull/2316/)


0.149.1 - 2022-12-09
--------------------

This release improves the performance of rich exceptions on custom scalars
by changing how frames are fetched from the call stack.
Before the change, custom scalars were using a CPU intensive call to the
`inspect` module to fetch frame info which could lead to serious CPU spikes.

Contributed by [Paulo Amaral](https://github.com/paulopaixaoamaral) via [PR #2390](https://github.com/strawberry-graphql/strawberry/pull/2390/)


0.149.0 - 2022-12-09
--------------------

This release does some internal refactoring of the HTTP views, hopefully it
doesn't affect anyone. It mostly changes the status codes returned in case of
errors (e.g. bad JSON, missing queries and so on).

It also improves the testing, and adds an entirely new test suite for the HTTP
views, this means in future we'll be able to keep all the HTTP views in sync
feature-wise.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1840](https://github.com/strawberry-graphql/strawberry/pull/1840/)


0.148.0 - 2022-12-08
--------------------

This release changes the `get_context`, `get_root_value` and `process_result`
methods of the Flask async view to be async functions. This allows you to use
async code in these methods.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2388](https://github.com/strawberry-graphql/strawberry/pull/2388/)


0.147.0 - 2022-12-08
--------------------

This release introduces a `encode_json` method on all the HTTP integrations.
This method allows to customize the encoding of the JSON response. By default we
use `json.dumps` but you can override this method to use a different encoder.

It also deprecates `json_encoder` and `json_dumps_params` in the Django and
Sanic views, `encode_json` should be used instead.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2272](https://github.com/strawberry-graphql/strawberry/pull/2272/)


0.146.0 - 2022-12-05
--------------------

This release updates the Sanic integration and includes some breaking changes.
You might need to update your code if you are customizing `get_context` or
`process_result`

## `get_context`

`get_context` now receives the request as the first argument and the response as
the second argument.

## `process_result`

`process_result` is now async and receives the request and the GraphQL execution
result.

This change is needed to align all the HTTP integrations and reduce the amount
of code needed to maintain. It also makes the errors consistent with other
integrations.

It also brings a **new feature** and it allows to customize the HTTP status code
by using `info.context["response"].status_code = YOUR_CODE`.

It also removes the upper bound on the Sanic version, so you can use the latest
version of Sanic with Strawberry.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2273](https://github.com/strawberry-graphql/strawberry/pull/2273/)


0.145.0 - 2022-12-04
--------------------

This release introduced improved errors! Now, when you have a syntax error in
your code, you'll get a nice error message with a line number and a pointer to
the exact location of the error. ✨

This is a huge improvement over the previous behavior, which was providing a
stack trace with no clear indication of where the error was. 🙈

You can enable rich errors by installing Strawberry with the `cli` extra:

```bash
pip install "strawberry-graphql[cli]"
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2027](https://github.com/strawberry-graphql/strawberry/pull/2027/)


0.144.3 - 2022-12-04
--------------------

This release fixes an issue with type duplication of generics.

You can now use a lazy type with a generic even if
the original type was already used with that generic in the schema.

Example:

```python
@strawberry.type
class Query:
    regular: Edge[User]
    lazy: Edge[Annotated["User", strawberry.lazy(".user")]]
```

Contributed by [Dmitry Semenov](https://github.com/lonelyteapot) via [PR #2381](https://github.com/strawberry-graphql/strawberry/pull/2381/)


0.144.2 - 2022-12-02
--------------------

Generic types are now allowed in the schema's extra types.
```python
T = TypeVar("T")


@strawberry.type
class Node(Generic[T]):
    field: T


@strawberry.type
class Query:
    name: str


schema = strawberry.Schema(Query, types=[Node[int]])
```

Contributed by [A. Coady](https://github.com/coady) via [PR #2294](https://github.com/strawberry-graphql/strawberry/pull/2294/)


0.144.1 - 2022-12-02
--------------------

This release fixes a regression that prevented Generic types
from being used multiple types.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2378](https://github.com/strawberry-graphql/strawberry/pull/2378/)


0.144.0 - 2022-12-02
--------------------

Added extra validation that types used in a schema are unique.
Strawberry starts to throw an exception `DuplicatedTypeName` when two types defined in a schema have the same name.

Contributed by [Bartosz Polnik](https://github.com/bartekbp) via [PR #2356](https://github.com/strawberry-graphql/strawberry/pull/2356/)


0.143.0 - 2022-12-01
--------------------

Added an error to be used when overriding GraphQLError in custom extensions and added a guide on how to use it.
Exposing GraphQLError from the strawberry namespace brings a better experience and will be useful in the future (when we move to something else).

Contributed by [Niten Nashiki](https://github.com/nnashiki) via [PR #2360](https://github.com/strawberry-graphql/strawberry/pull/2360/)


0.142.3 - 2022-11-29
--------------------

This release updates GraphiQL to 2.2.0 and fixes an issue with the websocket URL
being incorrectly set when navigating to GraphiQL with an URL with a hash.

Contributed by [Shen Li](https://github.com/ericls) via [PR #2363](https://github.com/strawberry-graphql/strawberry/pull/2363/)


0.142.2 - 2022-11-15
--------------------

This release changes the dataloader batch resolution to avoid resolving
futures that were canceled, and also from reusing them from the cache.
Trying to resolve a future that was canceled would raise `asyncio.InvalidStateError`

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2339](https://github.com/strawberry-graphql/strawberry/pull/2339/)


0.142.1 - 2022-11-11
--------------------

This release fixes a bug where using a custom scalar in a union would result
in an unclear exception. Instead, when using a custom scalar in a union,
the `InvalidUnionType` exception is raised with a clear message that you
cannot use that type in a union.

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2336](https://github.com/strawberry-graphql/strawberry/pull/2336/)


0.142.0 - 2022-11-11
--------------------

This release adds support for `typing.Self` and `typing_extensions.Self` for types and interfaces.

```python
from typing_extensions import Self


@strawberry.type
class Node:
    @strawberry.field
    def field(self) -> Self:
        return self
```

Contributed by [A. Coady](https://github.com/coady) via [PR #2295](https://github.com/strawberry-graphql/strawberry/pull/2295/)


0.141.0 - 2022-11-10
--------------------

This release adds support for an implicit `resolve_reference` method
on Federation type. This method will automatically create a Strawberry
instance for a federation type based on the input data received, for
example, the following:

```python
@strawberry.federation.type(keys=["id"])
class Something:
    id: str


@strawberry.federation.type(keys=["upc"])
class Product:
    upc: str
    something: Something

    @staticmethod
    def resolve_reference(**data):
        return Product(upc=data["upc"], something=Something(id=data["something_id"]))
```

doesn't need the resolve_reference method anymore.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2332](https://github.com/strawberry-graphql/strawberry/pull/2332/)


0.140.3 - 2022-11-09
--------------------

[Internal] Update StrawberryField so that `type_annotation` is always an instance of StrawberryAnnotation.

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2319](https://github.com/strawberry-graphql/strawberry/pull/2319/)


0.140.2 - 2022-11-08
--------------------

This release fixes an issue that prevented using enums that
were using strawberry.enum_value, like the following example:

```python
from enum import Enum
import strawberry


@strawberry.enum
class TestEnum(Enum):
    A = strawberry.enum_value("A")
    B = "B"


@strawberry.type
class Query:
    @strawberry.field
    def receive_enum(self, test: TestEnum) -> int:
        return 0


schema = strawberry.Schema(query=Query)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2306](https://github.com/strawberry-graphql/strawberry/pull/2306/)


0.140.1 - 2022-11-08
--------------------

This release adds logging back for parsing and validation errors that was
accidentally removed in v0.135.0.

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2323](https://github.com/strawberry-graphql/strawberry/pull/2323/)


0.140.0 - 2022-11-07
--------------------

This release allows to disable operation logging when running the debug server.

```
strawberry server demo --log-operations False
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2310](https://github.com/strawberry-graphql/strawberry/pull/2310/)


0.139.0 - 2022-11-04
--------------------

This release changes the type resolution priority to prefer the field annotation over the resolver return type.

```python
def my_resolver() -> str:
    return "1.33"


@strawberry.type
class Query:
    a: float = strawberry.field(resolver=my_resolver)


schema = strawberry.Schema(Query)

# Before:
str(
    schema
) == """
type Query {
  a: String!
}
"""

# After:
str(
    schema
) == """
type Query {
  a: Float!
}
"""
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2312](https://github.com/strawberry-graphql/strawberry/pull/2312/)


0.138.2 - 2022-11-04
--------------------

Fix Pydantic integration for Python 3.10.0 (which was missing the `kw_only`
parameter for `dataclasses.make_dataclass()`).

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2309](https://github.com/strawberry-graphql/strawberry/pull/2309/)


0.138.1 - 2022-10-31
--------------------

This release changes an internal implementation for FastAPI's
GraphQL router. This should reduce overhead when using the context,
and it shouldn't affect your code.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #2278](https://github.com/strawberry-graphql/strawberry/pull/2278/)


0.138.0 - 2022-10-31
--------------------

This release adds support for generic in arguments, see the following example:

```python
T = TypeVar("T")


@strawberry.type
class Node(Generic[T]):
    @strawberry.field
    def data(self, arg: T) -> T:  # `arg` is also generic
        return arg
```

Contributed by [A. Coady](https://github.com/coady) via [PR #2293](https://github.com/strawberry-graphql/strawberry/pull/2293/)


0.137.1 - 2022-10-24
--------------------

Allowed `CustomScalar | None` syntax for python >= 3.10.

Contributed by [Guillaume Andreu Sabater](https://github.com/g-as) via [PR #2279](https://github.com/strawberry-graphql/strawberry/pull/2279/)


0.137.0 - 2022-10-21
--------------------

This release fixes errors when using Union-of-lazy-types

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #2271](https://github.com/strawberry-graphql/strawberry/pull/2271/)


0.136.0 - 2022-10-21
--------------------

This release refactors the chalice integration in order to keep it consistent with
the other integrations.

## Deprecation:

Passing `render_graphiql` is now deprecated, please use `graphiql` instead.

## New features:

- You can now return a custom status by using `info.context["response"].status_code = 418`
- You can enabled/disable queries via get using `allow_queries_via_get` (defaults to `True`)

## Changes:

Trying to access /graphql via a browser and with `graphiql` set to `False` will return a 404.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2266](https://github.com/strawberry-graphql/strawberry/pull/2266/)


0.135.0 - 2022-10-21
--------------------

This release adds a new `MaskErrors` extension that can be used to hide error
messages from the client to prevent exposing sensitive details. By default it
masks all errors raised in any field resolver.

```python
import strawberry
from strawberry.extensions import MaskErrors

schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(),
    ],
)
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2248](https://github.com/strawberry-graphql/strawberry/pull/2248/)


0.134.5 - 2022-10-20
--------------------

This release improves the error message that you get when trying
to use an enum that hasn't been decorated with `@strawberry.enum`
inside a type's field.

Contributed by [Rise Riyo](https://github.com/riseriyo) via [PR #2267](https://github.com/strawberry-graphql/strawberry/pull/2267/)


0.134.4 - 2022-10-20
--------------------

This release adds support for printing schema directives on an input type object, for example the following schema:

```python
@strawberry.schema_directive(locations=[Location.INPUT_FIELD_DEFINITION])
class RangeInput:
    min: int
    max: int


@strawberry.input
class CreateUserInput:
    name: str
    age: int = strawberry.field(directives=[RangeInput(min=1, max=100)])
```

prints the following:

```graphql
directive @rangeInput(min: Int!, max: Int!) on INPUT_FIELD_DEFINITION

input Input @sensitiveInput(reason: "GDPR") {
  firstName: String!
  age: Int! @rangeInput(min: 1, max: 100)
}
```

Contributed by [Etty](https://github.com/estyxx) via [PR #2233](https://github.com/strawberry-graphql/strawberry/pull/2233/)


0.134.3 - 2022-10-16
--------------------

This release fixes an issue that prevented using strawberry.lazy with relative paths.

The following should work now:

```python
@strawberry.type
class TypeA:
    b: Annotated["TypeB", strawberry.lazy(".type_b")]
```

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #2244](https://github.com/strawberry-graphql/strawberry/pull/2244/)


0.134.2 - 2022-10-16
--------------------

This release adds pyupgrade to our CI and includes some minor changes to keep our codebase modern.

Contributed by [Liel Fridman](https://github.com/lielfr) via [PR #2255](https://github.com/strawberry-graphql/strawberry/pull/2255/)


0.134.1 - 2022-10-14
--------------------

This release fixes an issue that prevented using lazy types inside
generic types.

The following is now allowed:

```python
T = TypeVar("T")

TypeAType = Annotated["TypeA", strawberry.lazy("tests.schema.test_lazy.type_a")]


@strawberry.type
class Edge(Generic[T]):
    node: T


@strawberry.type
class Query:
    users: Edge[TypeAType]
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2254](https://github.com/strawberry-graphql/strawberry/pull/2254/)


0.134.0 - 2022-10-14
--------------------

These release allow you to define a different `url` in the `GraphQLTestClient`, the default is "/graphql/".

Here's an example with Starlette client:
```python
import pytest

from starlette.testclient import TestClient
from strawberry.asgi.test import GraphQLTestClient


@pytest.fixture
def graphql_client() -> GraphQLTestClient:
    return GraphQLTestClient(
        TestClient(app, base_url="http://localhost:8000"), url="/api/"
    )
```

Contributed by [Etty](https://github.com/estyxx) via [PR #2238](https://github.com/strawberry-graphql/strawberry/pull/2238/)


0.133.7 - 2022-10-14
--------------------

This release fixes a type issue when passing `scalar_overrides` to `strawberry.Schema`

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2251](https://github.com/strawberry-graphql/strawberry/pull/2251/)


0.133.6 - 2022-10-13
--------------------

Fix support for arguments where `arg.type=LazyType["EnumType"]`

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #2245](https://github.com/strawberry-graphql/strawberry/pull/2245/)


0.133.5 - 2022-10-03
--------------------

Updated `unset` import, from `strawberry.arguments` to `strawberry.unset` in codebase.

This will prevent strawberry from triggering its own warning on deprecated imports.

Contributed by [dependabot](https://github.com/dependabot) via [PR #2219](https://github.com/strawberry-graphql/strawberry/pull/2219/)


0.133.4 - 2022-10-03
--------------------

This release fixes the type of strawberry.federation.field,
this will prevent errors from mypy and pyright when doing the following:

```python
@strawberry.federation.type(keys=["id"])
class Location:
    id: strawberry.ID

    # the following field was reporting an error in mypy and pylance
    celestial_body: CelestialBody = strawberry.federation.field(
        resolver=resolve_celestial_body
    )
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2222](https://github.com/strawberry-graphql/strawberry/pull/2222/)


0.133.3 - 2022-10-03
--------------------

This release allows to create a federation schema without having to pass a
`Query` type. This is useful when your schema only extends some types without
adding any additional root field.

```python
@strawberry.federation.type(keys=["id"])
class Location:
    id: strawberry.ID
    name: str = strawberry.federation.field(override="start")


schema = strawberry.federation.Schema(types=[Location])
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2220](https://github.com/strawberry-graphql/strawberry/pull/2220/)


0.133.2 - 2022-09-30
--------------------

This release fixes an issue with `strawberry.federation.field` that
prevented instantiating field when passing a resolver function.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2218](https://github.com/strawberry-graphql/strawberry/pull/2218/)


0.133.1 - 2022-09-28
--------------------

This release fixes an issue that prevented using `strawberry.field` with
`UNSET` as the default value.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2128](https://github.com/strawberry-graphql/strawberry/pull/2128/)


0.133.0 - 2022-09-27
--------------------

Reduce the number of required dependencies, by marking Pygments and python-multipart as optional. These dependencies are still necessary for some functionality, and so users of that functionality need to ensure they're installed, either explicitly or via an extra:

- Pygments is still necessary when using Strawberry in debug mode, and is included in the `strawberry[debug-server]` extra.
- python-multipart is still necessary when using `strawberry.file_uploads.Upload` with FastAPI or Starlette, and is included in the `strawberry[fastapi]` and `strawberry[asgi]` extras, respectively.

There is now also the `strawberry[cli]` extra to support commands like `strawberry codegen` and `strawberry export-schema`.

Contributed by [Huon Wilson](https://github.com/huonw) via [PR #2205](https://github.com/strawberry-graphql/strawberry/pull/2205/)


0.132.1 - 2022-09-23
--------------------

Improve resolving performance by avoiding extra calls for basic fields.

This change improves performance of resolving a query by skipping `Info`
creation and permission checking for fields that don't have a resolver
or permission classes. In local benchmarks it improves performance of large
results by ~14%.

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2194](https://github.com/strawberry-graphql/strawberry/pull/2194/)


0.132.0 - 2022-09-23
--------------------

Support storing metadata in strawberry fields.

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #2190](https://github.com/strawberry-graphql/strawberry/pull/2190/)


0.131.5 - 2022-09-22
--------------------

Fixes false positives with the mypy plugin.
Happened when `to_pydantic` was called on a type that was converted
pydantic with all_fields=True.

Also fixes the type signature when `to_pydantic` is defined by the user.

```python
from pydantic import BaseModel
from typing import Optional
import strawberry


class MyModel(BaseModel):
    email: str
    password: Optional[str]


@strawberry.experimental.pydantic.input(model=MyModel, all_fields=True)
class MyModelStrawberry: ...


MyModelStrawberry(email="").to_pydantic()
# previously would complain wrongly about missing email and password
```

Contributed by [James Chua](https://github.com/thejaminator) via [PR #2017](https://github.com/strawberry-graphql/strawberry/pull/2017/)


0.131.4 - 2022-09-22
--------------------

This release updates the mypy plugin and the typing for Pyright to treat all
strawberry fields as keyword-only arguments. This reflects a previous change to
the Strawberry API.

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #2191](https://github.com/strawberry-graphql/strawberry/pull/2191/)


0.131.3 - 2022-09-22
--------------------

Bug fix: Do not force kw-only=False in fields specified with strawberry.field()

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #2189](https://github.com/strawberry-graphql/strawberry/pull/2189/)


0.131.2 - 2022-09-22
--------------------

This release fixes a small issue that might happen when
uploading files and not passing the operations object.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2192](https://github.com/strawberry-graphql/strawberry/pull/2192/)


0.131.1 - 2022-09-16
--------------------

Fix warnings during unit tests for Sanic's upload.

Otherwise running unit tests results in a bunch of warning like this:

```
DeprecationWarning: Use 'content=<...>' to upload raw bytes/text content.
```

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #2178](https://github.com/strawberry-graphql/strawberry/pull/2178/)


0.131.0 - 2022-09-15
--------------------

This release improves the dataloader class with new features:

- Explicitly cache invalidation, prevents old data from being fetched after a mutation
- Importing data into the cache, prevents unnecessary load calls if the data has already been fetched by other means.

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #2149](https://github.com/strawberry-graphql/strawberry/pull/2149/)


0.130.4 - 2022-09-14
--------------------

This release adds improved support for Pyright and Pylance, VSCode default
language server for Python.

Using `strawberry.type`, `strawberry.field`, `strawberry.input` and
`strawberry.enum` will now be correctly recognized by Pyright and Pylance and
won't show errors.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2172](https://github.com/strawberry-graphql/strawberry/pull/2172/)


0.130.3 - 2022-09-12
--------------------

Fix invalid deprecation warning issued on arguments annotated
by a subclassed `strawberry.types.Info`.

Thanks to @ThirVondukr for the bug report!

Example:

```python
class MyInfo(Info):
    pass


@strawberry.type
class Query:
    @strawberry.field
    def is_tasty(self, info: MyInfo) -> bool:
        """Subclassed ``info`` argument no longer raises deprecation warning."""
```

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #2137](https://github.com/strawberry-graphql/strawberry/pull/2137/)


0.130.2 - 2022-09-12
--------------------

This release fixes the conversion of generic aliases when
using pydantic.

Contributed by [Silas Sewell](https://github.com/silas) via [PR #2152](https://github.com/strawberry-graphql/strawberry/pull/2152/)


0.130.1 - 2022-09-12
--------------------

Fix version parsing issue related to dev builds of Mypy in `strawberry.ext.mypy_plugin`

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #2157](https://github.com/strawberry-graphql/strawberry/pull/2157/)


0.130.0 - 2022-09-12
--------------------

Convert Tuple and Sequence types to GraphQL list types.

Example:

```python
from collections.abc import Sequence
from typing import Tuple


@strawberry.type
class User:
    pets: Sequence[Pet]
    favourite_ice_cream_flavours: Tuple[IceCreamFlavour]
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #2164](https://github.com/strawberry-graphql/strawberry/pull/2164/)


0.129.0 - 2022-09-11
--------------------

This release adds `strawberry.lazy` which allows you to define the type of the
field and its path. This is useful when you want to define a field with a type
that has a circular dependency.

For example, let's say we have a `User` type that has a list of `Post` and a
`Post` type that has a `User`:

```python
# posts.py
from typing import TYPE_CHECKING, Annotated

import strawberry

if TYPE_CHECKING:
    from .users import User


@strawberry.type
class Post:
    title: str
    author: Annotated["User", strawberry.lazy(".users")]
```

```python
# users.py
from typing import TYPE_CHECKING, Annotated, List

import strawberry

if TYPE_CHECKING:
    from .posts import Post


@strawberry.type
class User:
    name: str
    posts: List[Annotated["Post", strawberry.lazy(".posts")]]
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2158](https://github.com/strawberry-graphql/strawberry/pull/2158/)


0.128.0 - 2022-09-05
--------------------

This release changes how dataclasses are created to make use of the new
`kw_only` argument in Python 3.10 so that fields without a default value can now
follow a field with a default value. This feature is also backported to all other
supported Python versions.

More info: https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass

For example:

```python
# This no longer raises a TypeError


@strawberry.type
class MyType:
    a: str = "Hi"
    b: int
```

⚠️ This is a breaking change! Whenever instantiating a Strawberry type make sure
that you only pass values are keyword arguments:

```python
# Before:

MyType("foo", 3)

# After:

MyType(a="foo", b=3)
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) via [PR #1187](https://github.com/strawberry-graphql/strawberry/pull/1187/)


0.127.4 - 2022-08-31
--------------------

This release fixes a bug in the subscription clean up when subscribing using the
graphql-transport-ws protocol, which could occasionally cause a 'finally'
statement within the task to not get run, leading to leaked resources.

Contributed by [rjwills28](https://github.com/rjwills28) via [PR #2141](https://github.com/strawberry-graphql/strawberry/pull/2141/)


0.127.3 - 2022-08-30
--------------------

This release fixes a couple of small styling issues with
the GraphiQL explorer

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2143](https://github.com/strawberry-graphql/strawberry/pull/2143/)


0.127.2 - 2022-08-30
--------------------

This release adds support for passing schema directives to
`Schema(..., types=[])`. This can be useful if using a built-inschema directive
that's not supported by a gateway.

For example the following:

```python
import strawberry
from strawberry.scalars import JSON
from strawberry.schema_directive import Location


@strawberry.type
class Query:
    example: JSON


@strawberry.schema_directive(locations=[Location.SCALAR], name="specifiedBy")
class SpecifiedBy:
    name: str


schema = strawberry.Schema(query=Query, types=[SpecifiedBy])
```

will print the following SDL:

```graphql
directive @specifiedBy(name: String!) on SCALAR

"""
The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
"""
scalar JSON
  @specifiedBy(
    url: "https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf"
  )

type Query {
  example: JSON!
}
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2140](https://github.com/strawberry-graphql/strawberry/pull/2140/)


0.127.1 - 2022-08-30
--------------------

This release fixes an issue with the updated GraphiQL
interface.

Contributed by [Doctor](https://github.com/ThirVondukr) via [PR #2138](https://github.com/strawberry-graphql/strawberry/pull/2138/)


0.127.0 - 2022-08-29
--------------------

This release updates the built-in GraphiQL version to version 2.0,
which means you can now enjoy all the new features that come with the latest version!

Contributed by [Matt Exact](https://github.com/MattExact) via [PR #1889](https://github.com/strawberry-graphql/strawberry/pull/1889/)


0.126.2 - 2022-08-23
--------------------

This release restricts the `backports.cached_property` dependency to only be
installed when Python < 3.8. Since version 3.8 `cached_property` is included
in the builtin `functools`. The code is updated to use the builtin version
when Python >= 3.8.

Contributed by [ljnsn](https://github.com/ljnsn) via [PR #2114](https://github.com/strawberry-graphql/strawberry/pull/2114/)


0.126.1 - 2022-08-22
--------------------

Keep extra discovered types sorted so that each schema printing is
always the same.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2115](https://github.com/strawberry-graphql/strawberry/pull/2115/)


0.126.0 - 2022-08-18
--------------------

This release adds support for adding descriptions to enum values.

### Example


```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = strawberry.enum_value("vanilla")
    STRAWBERRY = strawberry.enum_value(
        "strawberry",
        description="Our favourite",
    )
    CHOCOLATE = "chocolate"


@strawberry.type
class Query:
    favorite_ice_cream: IceCreamFlavour = IceCreamFlavour.STRAWBERRY


schema = strawberry.Schema(query=Query)
```

This produces the following schema

```graphql
enum IceCreamFlavour {
  VANILLA

  """Our favourite."""
  STRAWBERRY
  CHOCOLATE
}

type Query {
  favoriteIceCream: IceCreamFlavour!
}
```

Contributed by [Felipe Gonzalez](https://github.com/gonzalezzfelipe) via [PR #2106](https://github.com/strawberry-graphql/strawberry/pull/2106/)


0.125.1 - 2022-08-16
--------------------

This release hides `resolvable: True` in @keys directives
when using Apollo Federation 1, to preserve compatibility
with older Gateways.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2099](https://github.com/strawberry-graphql/strawberry/pull/2099/)


0.125.0 - 2022-08-12
--------------------

This release adds an integration with Django Channels. The integration will
allow you to use GraphQL subscriptions via Django Channels.

Contributed by [Dan Sloan](https://github.com/LucidDan) via [PR #1407](https://github.com/strawberry-graphql/strawberry/pull/1407/)


0.124.0 - 2022-08-08
--------------------

This release adds full support for Apollo Federation 2.0. To opt-in you need to
pass `enable_federation_2=True` to `strawberry.federation.Schema`, like in the
following example:

```python
@strawberry.federation.type(keys=["id"])
class User:
    id: strawberry.ID


@strawberry.type
class Query:
    user: User


schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)
```

This release also improves type checker support for the federation.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2047](https://github.com/strawberry-graphql/strawberry/pull/2047/)


0.123.3 - 2022-08-02
--------------------

This release fixes a regression introduced in version 0.118.2 which was
preventing using circular dependencies in Strawberry django and Strawberry
django plus.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #2062](https://github.com/strawberry-graphql/strawberry/pull/2062/)


0.123.2 - 2022-08-01
--------------------

This release adds support for priting custom enums used only on
schema directives, for example the following schema:

```python
@strawberry.enum
class Reason(str, Enum):
    EXAMPLE = "example"


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Sensitive:
    reason: Reason


@strawberry.type
class Query:
    first_name: str = strawberry.field(directives=[Sensitive(reason=Reason.EXAMPLE)])
```

prints the following:

```graphql
directive @sensitive(reason: Reason!) on FIELD_DEFINITION

type Query {
    firstName: String! @sensitive(reason: EXAMPLE)
}

enum Reason {
    EXAMPLE
}
```

while previously it would omit the definition of the enum.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2059](https://github.com/strawberry-graphql/strawberry/pull/2059/)


0.123.1 - 2022-08-01
--------------------

This release adds support for priting custom scalar used only on
schema directives, for example the following schema:

```python
SensitiveConfiguration = strawberry.scalar(str, name="SensitiveConfiguration")


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Sensitive:
    config: SensitiveConfiguration


@strawberry.type
class Query:
    first_name: str = strawberry.field(directives=[Sensitive(config="Some config")])
```

prints the following:

```graphql
directive @sensitive(config: SensitiveConfiguration!) on FIELD_DEFINITION

type Query {
    firstName: String! @sensitive(config: "Some config")
}

scalar SensitiveConfiguration
```

while previously it would omit the definition of the scalar.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2058](https://github.com/strawberry-graphql/strawberry/pull/2058/)


0.123.0 - 2022-08-01
--------------------

This PR adds support for adding schema directives to the schema of
your GraphQL API. For printing the following schema:

```python
@strawberry.schema_directive(locations=[Location.SCHEMA])
class Tag:
    name: str


@strawberry.type
class Query:
    first_name: str = strawberry.field(directives=[Tag(name="team-1")])


schema = strawberry.Schema(query=Query, schema_directives=[Tag(name="team-1")])
```

will print the following:

```graphql
directive @tag(name: String!) on SCHEMA

schema @tag(name: "team-1") {
    query: Query
}

type Query {
    firstName: String!
}
"""
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2054](https://github.com/strawberry-graphql/strawberry/pull/2054/)


0.122.1 - 2022-07-31
--------------------

This release fixes that the AIOHTTP integration ignored the `operationName` of query
operations. This behaviour is a regression introduced in version 0.107.0.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) via [PR #2055](https://github.com/strawberry-graphql/strawberry/pull/2055/)


0.122.0 - 2022-07-29
--------------------

This release adds support for printing default values for scalars like JSON.

For example the following:

```python
import strawberry
from strawberry.scalars import JSON


@strawberry.input
class MyInput:
    j: JSON = strawberry.field(default_factory=dict)
    j2: JSON = strawberry.field(default_factory=lambda: {"hello": "world"})
```

will print the following schema:

```graphql
input MyInput {
    j: JSON! = {}
    j2: JSON! = {hello: "world"}
}
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2048](https://github.com/strawberry-graphql/strawberry/pull/2048/)


0.121.1 - 2022-07-27
--------------------

This release adds a backward compatibility layer with libraries
that specify a custom `get_result`.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2038](https://github.com/strawberry-graphql/strawberry/pull/2038/)


0.121.0 - 2022-07-23
--------------------

This release adds support for overriding the default resolver for fields.

Currently the default resolver is `getattr`, but now you can change it to any
function you like, for example you can allow returning dictionaries:

```python
@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return {"name": "Patrick"}  # type: ignore


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(default_resolver=getitem),
)

query = "{ user { name } }"

result = schema.execute_sync(query)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2037](https://github.com/strawberry-graphql/strawberry/pull/2037/)


0.120.0 - 2022-07-23
--------------------

This release add a new `DatadogTracingExtension` that can be used to instrument
your application with Datadog.

```python
import strawberry

from strawberry.extensions.tracing import DatadogTracingExtension

schema = strawberry.Schema(
    Query,
    extensions=[
        DatadogTracingExtension,
    ],
)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #2001](https://github.com/strawberry-graphql/strawberry/pull/2001/)


0.119.2 - 2022-07-23
--------------------

Fixed edge case where `Union` types raised an `UnallowedReturnTypeForUnion`
error when returning the correct type from the resolver. This also improves
performance of StrawberryUnion's `_resolve_union_type` from `O(n)` to `O(1)` in
the majority of cases where `n` is the number of types in the schema.

For
[example the below](https://play.strawberry.rocks/?gist=f7d88898d127e65b12140fdd763f9ef2))
would previously raise the error when querying `two` as `StrawberryUnion` would
incorrectly determine that the resolver returns `Container[TypeOne]`.

```python
import strawberry
from typing import TypeVar, Generic, Union, List, Type

T = TypeVar("T")


@strawberry.type
class Container(Generic[T]):
    items: List[T]


@strawberry.type
class TypeOne:
    attr: str


@strawberry.type
class TypeTwo:
    attr: str


def resolver_one():
    return Container(items=[TypeOne("one")])


def resolver_two():
    return Container(items=[TypeTwo("two")])


@strawberry.type
class Query:
    one: Union[Container[TypeOne], TypeOne] = strawberry.field(resolver_one)
    two: Union[Container[TypeTwo], TypeTwo] = strawberry.field(resolver_two)


schema = strawberry.Schema(query=Query)
```

Contributed by [Tim OSullivan](https://github.com/invokermain) via [PR #2029](https://github.com/strawberry-graphql/strawberry/pull/2029/)


0.119.1 - 2022-07-18
--------------------

An explanatory custom exception is raised when union of GraphQL input types is attempted.

Contributed by [Dhanshree Arora](https://github.com/DhanshreeA) via [PR #2019](https://github.com/strawberry-graphql/strawberry/pull/2019/)


0.119.0 - 2022-07-14
--------------------

This release changes when we add the custom directives extension, previously
the extension was always enabled, now it is only enabled if you pass custom
directives to `strawberry.Schema`.

Contributed by [bomtall](https://github.com/bomtall) via [PR #2020](https://github.com/strawberry-graphql/strawberry/pull/2020/)


0.118.2 - 2022-07-14
--------------------

This release adds an initial fix to make `strawberry.auto` work when using
`from __future__ import annotations`.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1994](https://github.com/strawberry-graphql/strawberry/pull/1994/)


0.118.1 - 2022-07-14
--------------------

Fixes issue where users without pydantic were not able to use the mypy plugin.

Contributed by [James Chua](https://github.com/thejaminator) via [PR #2016](https://github.com/strawberry-graphql/strawberry/pull/2016/)


0.118.0 - 2022-07-13
--------------------

You can now pass keyword arguments to `to_pydantic`
```python
from pydantic import BaseModel
import strawberry


class MyModel(BaseModel):
    email: str
    password: str


@strawberry.experimental.pydantic.input(model=MyModel)
class MyModelStrawberry:
    email: strawberry.auto
    # no password field here


MyModelStrawberry(email="").to_pydantic(password="hunter")
```

Also if you forget to pass password, mypy will complain

```python
MyModelStrawberry(email="").to_pydantic()
# error: Missing named argument "password" for "to_pydantic" of "MyModelStrawberry"
```

Contributed by [James Chua](https://github.com/thejaminator) via [PR #2012](https://github.com/strawberry-graphql/strawberry/pull/2012/)


0.117.1 - 2022-07-07
--------------------

Allow to add alias to fields generated from pydantic with `strawberry.field(name="ageAlias")`.

```
class User(pydantic.BaseModel):
    age: int

@strawberry.experimental.pydantic.type(User)
class UserType:
    age: strawberry.auto = strawberry.field(name="ageAlias")
```

Contributed by [Alex](https://github.com/benzolium) via [PR #1986](https://github.com/strawberry-graphql/strawberry/pull/1986/)


0.117.0 - 2022-07-06
--------------------

This release fixes an issue that required installing opentelemetry when
trying to use the ApolloTracing extension

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1977](https://github.com/strawberry-graphql/strawberry/pull/1977/)


0.116.4 - 2022-07-04
--------------------

Fix regression caused by the new resolver argument handling mechanism
introduced in v0.115.0. This release restores the ability to use unhashable
default values in resolvers such as dict and list. See example below:

```python
@strawberry.type
class Query:
    @strawberry.field
    def field(self, x: List[str] = ["foo"], y: JSON = {"foo": 42}) -> str:  # noqa: B006
        return f"{x} {y}"
```

Thanks to @coady for the regression report!

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #1985](https://github.com/strawberry-graphql/strawberry/pull/1985/)


0.116.3 - 2022-07-04
--------------------

This release fixes the following error when trying to use Strawberry
with Apollo Federation:

```
Error: A valid schema couldn't be composed. The following composition errors were found:
	[burro-api] Unknown type _FieldSet
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1988](https://github.com/strawberry-graphql/strawberry/pull/1988/)


0.116.2 - 2022-07-03
--------------------

Reimplement `StrawberryResolver.annotations` property after removal in v0.115.

Library authors who previously relied on the public `annotations` property
can continue to do so after this fix.

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #1990](https://github.com/strawberry-graphql/strawberry/pull/1990/)


0.116.1 - 2022-07-03
--------------------

This release fixes a breaking internal error in mypy plugin for the following case.
- using positional arguments to pass a resolver for `strawberry.field()` or `strawberry.mutation()`

```python
failed: str = strawberry.field(resolver)
successed: str = strawberry.field(resolver=resolver)
```

now mypy returns an error with `"field()" or "mutation()" only takes keyword arguments` message
rather than an internal error.

Contributed by [cake-monotone](https://github.com/cake-monotone) via [PR #1987](https://github.com/strawberry-graphql/strawberry/pull/1987/)


0.116.0 - 2022-07-03
--------------------

This release adds a link from generated GraphQLCore types to the Strawberry type
that generated them.

From a GraphQLCore type you can now access the Strawberry type by doing:

```python
strawberry_type: TypeDefinition = graphql_core_type.extensions[
    GraphQLCoreConverter.DEFINITION_BACKREF
]
```

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #1766](https://github.com/strawberry-graphql/strawberry/pull/1766/)


0.115.0 - 2022-07-01
--------------------

This release changes how we declare the `info` argument in resolvers and the
`value` argument in directives.

Previously we'd use the name of the argument to determine its value. Now we use
the type annotation of the argument to determine its value.

Here's an example of how the old syntax works:

```python
def some_resolver(info) -> str:
    return info.context.get("some_key", "default")


@strawberry.type
class Example:
    a_field: str = strawberry.resolver(some_resolver)
```

and here's an example of how the new syntax works:

```python
from strawberry.types import Info


def some_resolver(info: strawberry.Info) -> str:
    return info.context.get("some_key", "default")


@strawberry.type
class Example:
    a_field: str = strawberry.resolver(some_resolver)
```

This means that you can now use a different name for the `info` argument in your
resolver and the `value` argument in your directive.

Here's an example that uses a custom name for both the value and the info
parameter in directives:

```python
from strawberry.types import Info
from strawberry.directive import DirectiveLocation, DirectiveValue


@strawberry.type
class Cake:
    frosting: Optional[str] = None
    flavor: str = "Chocolate"


@strawberry.type
class Query:
    @strawberry.field
    def cake(self) -> Cake:
        return Cake()


@strawberry.directive(
    locations=[DirectiveLocation.FIELD],
    description="Add frosting with ``value`` to a cake.",
)
def add_frosting(value: str, v: DirectiveValue[Cake], my_info: strawberry.Info):
    # Arbitrary argument name when using `DirectiveValue` is supported!
    assert isinstance(v, Cake)
    if (
        value in my_info.context["allergies"]
    ):  # Info can now be accessed from directives!
        raise AllergyError("You are allergic to this frosting!")
    else:
        v.frosting = value  # Value can now be used as a GraphQL argument name!
    return v
```

**Note:** the old way of passing arguments by name is deprecated and will be
removed in future releases of Strawberry.

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #1713](https://github.com/strawberry-graphql/strawberry/pull/1713/)


0.114.7 - 2022-07-01
--------------------

Allow use of implicit `Any` in `strawberry.Private` annotated Generic types.

For example the following is now supported:

```python
from __future__ import annotations

from typing import Generic, Sequence, TypeVar

import strawberry


T = TypeVar("T")


@strawberry.type
class Foo(Generic[T]):
    private_field: strawberry.Private[Sequence]  # instead of Sequence[Any]


@strawberry.type
class Query:
    @strawberry.field
    def foo(self) -> Foo[str]:
        return Foo(private_field=[1, 2, 3])
```

See Issue [#1938](https://github.com/strawberry-graphql/strawberry/issues/1938)
for details.

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #1939](https://github.com/strawberry-graphql/strawberry/pull/1939/)


0.114.6 - 2022-06-30
--------------------

The federation decorator now allows for a list of additional arbitrary schema
directives extending the key/shareable directives used for federation.

Example Python:

```python
import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.schema_directive import Location


@strawberry.schema_directive(locations=[Location.OBJECT])
class CacheControl:
    max_age: int


@strawberry.federation.type(
    keys=["id"], shareable=True, extend=True, directives=[CacheControl(max_age=42)]
)
class FederatedType:
    id: strawberry.ID


schema = strawberry.Schema(query=Query, config=StrawberryConfig(auto_camel_case=False))
```

Resulting GQL Schema:

```graphql
directive @CacheControl(max_age: Int!) on OBJECT
directive @key(fields: _FieldSet!, resolvable: Boolean) on OBJECT | INTERFACE
directive @shareable on FIELD_DEFINITION | OBJECT

extend type FederatedType
  @key(fields: "id")
  @shareable
  @CacheControl(max_age: 42) {
  id: ID!
}

type Query {
  federatedType: FederatedType!
}
```

Contributed by [Jeffrey DeFond](https://github.com/defond0) via [PR #1945](https://github.com/strawberry-graphql/strawberry/pull/1945/)


0.114.5 - 2022-06-23
--------------------

This release adds support in Mypy for using strawberry.mutation
while passing a resolver, the following now doesn't make Mypy return
an error:

```python
import strawberry


def set_name(self, name: str) -> None:
    self.name = name


@strawberry.type
class Mutation:
    set_name: None = strawberry.mutation(resolver=set_name)
```

Contributed by [Etty](https://github.com/estyxx) via [PR #1966](https://github.com/strawberry-graphql/strawberry/pull/1966/)


0.114.4 - 2022-06-23
--------------------

This release fixes the type annotation of `Response.errors` used in the `GraphQLTestClient` to be a `List` of `GraphQLFormattedError`.

Contributed by [Etty](https://github.com/estyxx) via [PR #1961](https://github.com/strawberry-graphql/strawberry/pull/1961/)


0.114.3 - 2022-06-21
--------------------

This release fixes the type annotation of `Response.errors` used in the `GraphQLTestClient` to be a `List` of `GraphQLError`.

Contributed by [Etty](https://github.com/estyxx) via [PR #1959](https://github.com/strawberry-graphql/strawberry/pull/1959/)


0.114.2 - 2022-06-15
--------------------

This release fixes an issue in the `GraphQLTestClient` when using both variables and files together.

Contributed by [Etty](https://github.com/estyxx) via [PR #1576](https://github.com/strawberry-graphql/strawberry/pull/1576/)


0.114.1 - 2022-06-09
--------------------

Fix crash in Django's `HttpResponse.__repr__` by handling `status_code=None` in `TemporalHttpResponse.__repr__`.

Contributed by [Daniel Hahler](https://github.com/blueyed) via [PR #1950](https://github.com/strawberry-graphql/strawberry/pull/1950/)


0.114.0 - 2022-05-27
--------------------

Improve schema directives typing and printing after latest refactor.

- Support for printing schema directives for non-scalars (e.g. types) and null values.
- Also print the schema directive itself and any extra types defined in it
- Fix typing for apis expecting directives (e.g. `strawberry.field`, `strawberry.type`, etc)
  to expect an object instead of a `StrawberrySchemaDirective`, which is now an internal type.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #1723](https://github.com/strawberry-graphql/strawberry/pull/1723/)


0.113.0 - 2022-05-19
--------------------

This release adds support for Starlette 0.18 to 0.20

It also removes upper bound dependencies limit for starlette,
allowing you to install the latest version without having to
wait for a new release of Strawberry

Contributed by [Timothy Pansino](https://github.com/TimPansino) via [PR #1594](https://github.com/strawberry-graphql/strawberry/pull/1594/)


0.112.0 - 2022-05-15
--------------------

This release adds a new flask view to allow for aysnc dispatching of requests.

This is especially useful when using dataloaders with flask.

```python
from strawberry.flask.views import AsyncGraphQLView

...

app.add_url_rule(
    "/graphql",
    view_func=AsyncGraphQLView.as_view("graphql_view", schema=schema, **kwargs),
)
```

Contributed by [Scott Weitzner](https://github.com/scottweitzner) via [PR #1907](https://github.com/strawberry-graphql/strawberry/pull/1907/)


0.111.2 - 2022-05-09
--------------------

This release fixes resolvers using functions with generic type variables raising a `MissingTypesForGenericError` error.

For example a resolver factory like the below can now be used:

```python
import strawberry
from typing import Type, TypeVar

T = TypeVar("T")  # or TypeVar("T", bound=StrawberryType) etc


def resolver_factory(strawberry_type: Type[T]):
    def resolver(id: strawberry.ID) -> T:
        # some actual logic here
        return strawberry_type(...)

    return resolver
```

Contributed by [Tim OSullivan](https://github.com/invokermain) via [PR #1891](https://github.com/strawberry-graphql/strawberry/pull/1891/)


0.111.1 - 2022-05-03
--------------------

Rename internal variable `custom_getter` in FastAPI router implementation.

Contributed by [Gary Donovan](https://github.com/garyd203) via [PR #1875](https://github.com/strawberry-graphql/strawberry/pull/1875/)


0.111.0 - 2022-05-02
--------------------

This release adds support for Apollo Federation 2 directives:
- @shareable
- @tag
- @override
- @inaccessible

This release does **not** add support for the @link directive.

This release updates the @key directive to align with Apollo Federation 2 updates.

See the below code snippet and/or the newly-added test cases for examples on how to use the new directives.
The below snippet demonstrates the @override directive.
```python
import strawberry
from typing import List


@strawberry.interface
class SomeInterface:
    id: strawberry.ID


@strawberry.federation.type(keys=["upc"], extend=True)
class Product(SomeInterface):
    upc: str = strawberry.federation.field(external=True, override=["mySubGraph"])


@strawberry.federation.type
class Query:
    @strawberry.field
    def top_products(self, first: int) -> List[Product]:
        return []


schema = strawberry.federation.Schema(query=Query)
```

should return:

```graphql
extend type Product implements SomeInterface @key(fields: "upc", resolvable: "True") {
  id: ID!
  upc: String! @external @override(from: "mySubGraph")
}

type Query {
  _service: _Service!
  _entities(representations: [_Any!]!): [_Entity]!
  topProducts(first: Int!): [Product!]!
}

interface SomeInterface {
  id: ID!
}

scalar _Any

union _Entity = Product

type _Service {
  sdl: String!
}
```

Contributed by [Matt Skillman](https://github.com/mtskillman) via [PR #1874](https://github.com/strawberry-graphql/strawberry/pull/1874/)


0.110.0 - 2022-05-02
--------------------

This release adds support for passing a custom name to schema directives fields,
by using `strawberry.directive_field`.

```python
import strawberry


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Sensitive:
    reason: str = strawberry.directive_field(name="as")
    real_age_2: str = strawberry.directive_field(name="real_age")


@strawberry.type
class Query:
    first_name: str = strawberry.field(
        directives=[Sensitive(reason="GDPR", real_age_2="42")]
    )
```

should return:

```graphql
type Query {
    firstName: String! @sensitive(as: "GDPR", real_age: "42")
}
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1871](https://github.com/strawberry-graphql/strawberry/pull/1871/)


0.109.1 - 2022-04-28
--------------------

This release adds support for Mypy 0.950

Contributed by [dependabot](https://github.com/dependabot) via [PR #1855](https://github.com/strawberry-graphql/strawberry/pull/1855/)


0.109.0 - 2022-04-23
--------------------

Changed the location of `UNSET` from `arguments.py` to `unset.py`. `UNSET` can now also be imported directly from `strawberry`. Deprecated the `is_unset` method in favor of the builtin `is` operator:

```python
from strawberry import UNSET
from strawberry.arguments import is_unset  # old

a = UNSET

assert a is UNSET  # new
assert is_unset(a)  # old
```
Further more a new subsection to the docs was added explaining this.

Contributed by [Dominique Garmier](https://github.com/DominiqueGarmier) via [PR #1813](https://github.com/strawberry-graphql/strawberry/pull/1813/)


0.108.3 - 2022-04-22
--------------------

Fixes a bug when converting pydantic models with NewTypes in a List.
This no longers causes an exception.

 ```python
 from typing import List, NewType
 from pydantic import BaseModel
 import strawberry

 password = NewType("password", str)


 class User(BaseModel):
     passwords: List[password]


 @strawberry.experimental.pydantic.type(User)
 class UserType:
     passwords: strawberry.auto
 ```

Contributed by [James Chua](https://github.com/thejaminator) via [PR #1770](https://github.com/strawberry-graphql/strawberry/pull/1770/)


0.108.2 - 2022-04-21
--------------------

Fixes mypy type inference when using @strawberry.experimental.pydantic.input
 and @strawberry.experimental.pydantic.interface decorators

Contributed by [James Chua](https://github.com/thejaminator) via [PR #1832](https://github.com/strawberry-graphql/strawberry/pull/1832/)


0.108.1 - 2022-04-20
--------------------

Refactoring: Move enum deserialization logic from convert_arguments to CustomGraphQLEnumType

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #1765](https://github.com/strawberry-graphql/strawberry/pull/1765/)


0.108.0 - 2022-04-19
--------------------

Added support for deprecating Enum values with `deprecation_reason` while using `strawberry.enum_value` instead of string definition.

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = strawberry.enum_value("vanilla")
    STRAWBERRY = strawberry.enum_value("strawberry", deprecation_reason="We ran out")
    CHOCOLATE = "chocolate"
```

Contributed by [Mateusz Sobas](https://github.com/msobas) via [PR #1720](https://github.com/strawberry-graphql/strawberry/pull/1720/)


0.107.1 - 2022-04-18
--------------------

This release fixes an issue in the previous release where requests using query params did not support passing variable values. Variables passed by query params are now parsed from a string to a dictionary.

Contributed by [Matt Exact](https://github.com/MattExact) via [PR #1820](https://github.com/strawberry-graphql/strawberry/pull/1820/)


0.107.0 - 2022-04-18
--------------------

This release adds support in all our integration for queries via GET requests.
This behavior is enabled by default, but you can disable it by passing
`allow_queries_via_get=False` to the constructor of the integration of your
choice.

For security reason only queries are allowed via `GET` requests.

Contributed by [Matt Exact](https://github.com/MattExact) via [PR #1686](https://github.com/strawberry-graphql/strawberry/pull/1686/)


0.106.3 - 2022-04-15
--------------------

Correctly parse Decimal scalar types to avoid floating point errors

Contributed by [Marco Acierno](https://github.com/marcoacierno) via [PR #1811](https://github.com/strawberry-graphql/strawberry/pull/1811/)


0.106.2 - 2022-04-14
--------------------

Allow all data types in `Schema(types=[...])`

Contributed by [Paulo Costa](https://github.com/paulo-raca) via [PR #1714](https://github.com/strawberry-graphql/strawberry/pull/1714/)


0.106.1 - 2022-04-14
--------------------

This release fixes a number of problems with single-result-operations over
`graphql-transport-ws` protocol

- operation **IDs** now share the same namespace as streaming operations
  meaning that they cannot be reused while the others are in operation

- single-result-operations now run as *tasks* meaning that messages related
  to them can be overlapped with other messages on the websocket.

- single-result-operations can be cancelled with the `complete` message.

- IDs for single result and streaming result operations are now released
  once the operation is done, allowing them to be re-used later, as well as
  freeing up resources related to previous requests.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #1792](https://github.com/strawberry-graphql/strawberry/pull/1792/)


0.106.0 - 2022-04-14
--------------------

This release adds an implementation of the `GraphQLTestClient` for the `aiohttp` integration (in addition to the existing `asgi` and `Django` support). It hides the HTTP request's details and verifies that there are no errors in the response (this behavior can be disabled by passing `asserts_errors=False`). This makes it easier to test queries and makes your tests cleaner.

If you are using `pytest` you can add a fixture in `conftest.py`

```python
import pytest

from strawberry.aiohttp.test.client import GraphQLTestClient


@pytest.fixture
def graphql_client(aiohttp_client, myapp):
    yield GraphQLTestClient(aiohttp_client(myapp))
```

And use it everywhere in your tests

```python
def test_strawberry(graphql_client):
    query = """
        query Hi($name: String!) {
            hi(name: $name)
        }
    """

    result = graphql_client.query(query, variables={"name": "🍓"})

    assert result.data == {"hi": "Hi 🍓!"}
```

Contributed by [Etty](https://github.com/estyxx) via [PR #1604](https://github.com/strawberry-graphql/strawberry/pull/1604/)


0.105.1 - 2022-04-12
--------------------

This release fixes a bug in the codegen that marked optional unions
as non optional.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1806](https://github.com/strawberry-graphql/strawberry/pull/1806/)


0.105.0 - 2022-04-05
--------------------

This release adds support for passing `json_encoder` and `json_dumps_params` to Sanic's view.


```python
from strawberry.sanic.views import GraphQLView

from api.schema import Schema

app = Sanic(__name__)

app.add_route(
    GraphQLView.as_view(
        schema=schema,
        graphiql=True,
        json_encoder=CustomEncoder,
        json_dumps_params={},
    ),
    "/graphql",
)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1797](https://github.com/strawberry-graphql/strawberry/pull/1797/)


0.104.4 - 2022-04-05
--------------------

Allow use of `AsyncIterator` and `AsyncIterable` generics to annotate return
type of subscription resolvers.

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #1771](https://github.com/strawberry-graphql/strawberry/pull/1771/)


0.104.3 - 2022-04-03
--------------------

Exeptions from handler functions in graphql_transport_ws are no longer
incorrectly caught and classified as message parsing errors.

Contributed by [Kristján Valur Jónsson](https://github.com/kristjanvalur) via [PR #1761](https://github.com/strawberry-graphql/strawberry/pull/1761/)


0.104.2 - 2022-04-02
--------------------

Drop support for Django < 3.2.

Contributed by [Guillaume Andreu Sabater](https://github.com/g-as) via [PR #1787](https://github.com/strawberry-graphql/strawberry/pull/1787/)


0.104.1 - 2022-03-28
--------------------

This release adds support for aliased fields when doing codegen.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1772](https://github.com/strawberry-graphql/strawberry/pull/1772/)


0.104.0 - 2022-03-28
--------------------

Add `is_auto` utility for checking if a type is `strawberry.auto`,
considering the possibility of it being a `StrawberryAnnotation` or
even being used inside `Annotated`.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) via [PR #1721](https://github.com/strawberry-graphql/strawberry/pull/1721/)


0.103.9 - 2022-03-23
--------------------

This release moves the console plugin for the codegen command
to be last one, allowing to run code before writing files to
disk.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1760](https://github.com/strawberry-graphql/strawberry/pull/1760/)


0.103.8 - 2022-03-18
--------------------

This release adds a `python_type` to the codegen `GraphQLEnum` class
to allow access to the original python enum when generating code

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1752](https://github.com/strawberry-graphql/strawberry/pull/1752/)


0.103.7 - 2022-03-18
--------------------

Fix an issue where there was no clean way to mark a Pydantic field as deprecated, add permission classes, or add directives. Now you can use the short field syntax to do all three.

```python
import pydantic
import strawberry


class MyModel(pydantic.BaseModel):
    age: int
    name: str


@strawberry.experimental.pydantic.type(MyModel)
class MyType:
    age: strawberry.auto
    name: strawberry.auto = strawberry.field(
        deprecation_reason="Because",
        permission_classes=[MyPermission],
        directives=[MyDirective],
    )
```

Contributed by [Matt Allen](https://github.com/Matt343) via [PR #1748](https://github.com/strawberry-graphql/strawberry/pull/1748/)


0.103.6 - 2022-03-18
--------------------

This release adds a missing `__init__.py` inside `cli/commands`

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1751](https://github.com/strawberry-graphql/strawberry/pull/1751/)


0.103.5 - 2022-03-18
--------------------

This release fixes an issue that prevented using generic types
with interfaces.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1701](https://github.com/strawberry-graphql/strawberry/pull/1701/)


0.103.4 - 2022-03-18
--------------------

This release fixes a couple of more issues with codegen:

1. Adds support for boolean values in input fields
2. Changes how we unwrap types in order to add full support for LazyTypes, Optionals and Lists
3. Improve also how we generate types for unions, now we don't generate a Union type if the selection is for only one type

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1746](https://github.com/strawberry-graphql/strawberry/pull/1746/)


0.103.3 - 2022-03-17
--------------------

The return type annotation for `DataLoader.load` and `load_many` no longer
includes any exceptions directly returned by the `load_fn`. The ability to
handle errors by returning them as elements from `load_fn` is now documented too.

Contributed by [Huon Wilson](https://github.com/huonw) via [PR #1737](https://github.com/strawberry-graphql/strawberry/pull/1737/)


0.103.2 - 2022-03-17
--------------------

This release add supports for `LazyType`s in the codegen command

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1745](https://github.com/strawberry-graphql/strawberry/pull/1745/)


0.103.1 - 2022-03-15
--------------------

This release adds support for MyPy 0.941 under Python 3.10

Contributed by [dependabot](https://github.com/dependabot) via [PR #1728](https://github.com/strawberry-graphql/strawberry/pull/1728/)


0.103.0 - 2022-03-14
--------------------

This release adds an experimental codegen feature for queries.
It allows to combine a graphql query and Strawberry schema to generate
Python types or TypeScript types.

You can use the following command:

```bash
strawberry codegen --schema schema --output-dir ./output -p python query.graphql
```

to generate python types that correspond to your GraphQL query.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1655](https://github.com/strawberry-graphql/strawberry/pull/1655/)


0.102.3 - 2022-03-14
--------------------

This release makes StrawberryOptional and StrawberryList hashable,
allowing to use strawberry types with libraries like dacite and
dataclasses_json.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1726](https://github.com/strawberry-graphql/strawberry/pull/1726/)


0.102.2 - 2022-03-08
--------------------

Add support for postponed evaluation of annotations
([PEP-563](https://www.python.org/dev/peps/pep-0563/)) to `strawberry.Private`
annotated fields.

## Example

This release fixes Issue #1586 using schema-conversion time filtering of
`strawberry.Private` fields for PEP-563. This means the following is now
supported:

```python
@strawberry.type
class Query:
    foo: "strawberry.Private[int]"
```

Forward references are supported as well:

```python
from __future__ import annotations

from dataclasses import dataclass


@strawberry.type
class Query:
    private_foo: strawberry.Private[SensitiveData]

    @strawberry.field
    def foo(self) -> int:
        return self.private_foo.visible


@dataclass
class SensitiveData:
    visible: int
    not_visible: int
```

Contributed by [San Kilkis](https://github.com/skilkis) via [PR #1684](https://github.com/strawberry-graphql/strawberry/pull/1684/)


0.102.1 - 2022-03-07
--------------------

This PR improves the support for scalars when using MyPy.

Contributed by [Patrick Arminio](https://github.com/patrick91) via [PR #1205](https://github.com/strawberry-graphql/strawberry/pull/1205/)


0.102.0 - 2022-03-07
--------------------

Added the response object to `get_context` on the `flask` view. This means that in fields, something like this can be used;

```python
@strawberry.field
def response_check(self, info: strawberry.Info) -> bool:
    response: Response = info.context["response"]
    response.status_code = 401

    return True
```

0.101.0 - 2022-03-06
--------------------

This release adds support for `graphql-transport-ws` single result operations.

Single result operations allow clients to execute queries and mutations over an existing WebSocket connection.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1698](https://github.com/strawberry-graphql/strawberry/pull/1698/)


0.100.0 - 2022-03-05
--------------------

Change `strawberry.auto` to be a type instead of a sentinel.
This not only removes the dependency on sentinel from the project, but also fixes
some related issues, like the fact that only types can be used with `Annotated`.

Also, custom scalars will now trick static type checkers into thinking they
returned their wrapped type. This should fix issues with pyright 1.1.224+ where
it doesn't allow non-type objects to be used as annotations for dataclasses and
dataclass-alike classes (which is strawberry's case). The change to `strawberry.auto`
also fixes this issue for it.

Contributed by [Thiago Bellini Ribeiro](https://github.com/bellini666) [PR #1690](https://github.com/strawberry-graphql/strawberry/pull/1690/)


0.99.3 - 2022-03-05
-------------------

This release adds support for flask 2.x and also relaxes the requirements for Django, allowing to install newer version of Django without having to wait for Strawberry to update its supported dependencies list.

Contributed by [Guillaume Andreu Sabater](https://github.com/g-as) [PR #1687](https://github.com/strawberry-graphql/strawberry/pull/1687/)


0.99.2 - 2022-03-04
-------------------

This fixes the schema printer to add support for schema
directives on input types.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1697](https://github.com/strawberry-graphql/strawberry/pull/1697/)


0.99.1 - 2022-03-02
-------------------

This release fixed a false positive deprecation warning related to our AIOHTTP class based view.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1691](https://github.com/strawberry-graphql/strawberry/pull/1691/)


0.99.0 - 2022-02-28
-------------------

This release adds the following scalar types:

- `JSON`
- `Base16`
- `Base32`
- `Base64`

they can be used like so:

```python
from strawberry.scalar import Base16, Base32, Base64, JSON


@strawberry.type
class Example:
    a: Base16
    b: Base32
    c: Base64
    d: JSON
```

Contributed by [Paulo Costa](https://github.com/paulo-raca) [PR #1647](https://github.com/strawberry-graphql/strawberry/pull/1647/)


0.98.2 - 2022-02-24
-------------------

Adds support for converting pydantic conlist.
Note that constraint is not enforced in the graphql type.
Thus, we recommend always working on the pydantic type such that the validation is enforced.

```python
import strawberry
from pydantic import BaseModel, conlist


class Example(BaseModel):
    friends: conlist(str, min_items=1)


@strawberry.experimental.pydantic.input(model=Example, all_fields=True)
class ExampleGQL: ...


@strawberry.type
class Query:
    @strawberry.field()
    def test(self, example: ExampleGQL) -> None:
        # friends may be an empty list here
        print(example.friends)
        # calling to_pydantic() runs the validation and raises
        # an error if friends is empty
        print(example.to_pydantic().friends)


schema = strawberry.Schema(query=Query)
```

The converted graphql type is
```
input ExampleGQL {
  friends: [String!]!
}
```

Contributed by [James Chua](https://github.com/thejaminator) [PR #1656](https://github.com/strawberry-graphql/strawberry/pull/1656/)

0.98.1 - 2022-02-24
-------------------

This release wasn't published on PyPI

0.98.0 - 2022-02-23
-------------------

This release updates `graphql-core` to `3.2.0`

Make sure you take a look at [`graphql-core`'s release notes](https://github.com/graphql-python/graphql-core/releases/tag/v3.2.0)
for any potential breaking change that might affect you if you're importing things
from the `graphql` package directly.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1601](https://github.com/strawberry-graphql/strawberry/pull/1601/)


0.97.0 - 2022-02-17
-------------------

Support "void" functions

It is now possible to have a resolver that returns "None". Strawberry will automatically assign the new `Void` scalar in the schema
and will always send `null` in the response

## Exampe

```python
@strawberry.type
class Mutation:
    @strawberry.field
    def do_something(self, arg: int) -> None:
        return
```
results in this schema:
```graphql
type Mutation {
    doSomething(arg: Int!): Void
}
```

Contributed by [Paulo Costa](https://github.com/paulo-raca) [PR #1648](https://github.com/strawberry-graphql/strawberry/pull/1648/)


0.96.0 - 2022-02-07
-------------------

Add better support for custom Pydantic conversion logic and standardize the
behavior when not using `strawberry.auto` as the type.

See https://strawberry.rocks/docs/integrations/pydantic#custom-conversion-logic for details and examples.

Note that this release fixes a bug related to Pydantic aliases in schema
generation. If you have a field with the same name as an aliased Pydantic field
but with a different type than `strawberry.auto`, the generated field will now
use the alias name. This may cause schema changes on upgrade in these cases, so
care should be taken. The alias behavior can be disabled by setting the
`use_pydantic_alias` option of the decorator to false.

Contributed by [Matt Allen](https://github.com/Matt343) [PR #1629](https://github.com/strawberry-graphql/strawberry/pull/1629/)


0.95.5 - 2022-02-07
-------------------

Adds support for `use_pydantic_alias` parameter in pydantic model conversion.
Decides if the all the GraphQL field names for the generated type should use the alias name or not.

```python
from pydantic import BaseModel, Field
import strawberry


class UserModel(BaseModel):
    id: int = Field(..., alias="my_alias_name")


@strawberry.experimental.pydantic.type(UserModel, use_pydantic_alias=False)
class User:
    id: strawberry.auto
```

If `use_pydantic_alias` is `False`, the GraphQL type User will use `id` for the name of the `id` field coming from the Pydantic model.
```
type User {
      id: Int!
}
```

With `use_pydantic_alias` set to `True` (the default behaviour) the GraphQL type user will use `myAliasName` for the `id` field coming from the Pydantic models (since the field has a `alias` specified`)
```
type User {
      myAliasName: Int!
}
```

`use_pydantic_alias` is set to `True` for backwards compatibility.

Contributed by [James Chua](https://github.com/thejaminator) [PR #1546](https://github.com/strawberry-graphql/strawberry/pull/1546/)


0.95.4 - 2022-02-06
-------------------

This release adds compatibility with uvicorn 0.17

Contributed by [dependabot](https://github.com/dependabot) [PR #1627](https://github.com/strawberry-graphql/strawberry/pull/1627/)


0.95.3 - 2022-02-03
-------------------

This release fixes an issue with FastAPI context dependency injection that causes class-based custom contexts to no longer be permitted.

Contributed by [Tommy Smith](https://github.com/tsmith023) [PR #1564](https://github.com/strawberry-graphql/strawberry/pull/1564/)


0.95.2 - 2022-02-02
-------------------

This release fixes an issue with the name generation for nested generics,
the following:

```python
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


@strawberry.type
class Value(Generic[T]):
    value: T


@strawberry.type
class DictItem(Generic[K, V]):
    key: K
    value: V


@strawberry.type
class Query:
    d: Value[List[DictItem[int, str]]]
```

now yields the correct schema:

```graphql
type IntStrDictItem {
  key: Int!
  value: String!
}

type IntStrDictItemListValue {
  value: [IntStrDictItem!]!
}

type Query {
  d: IntStrDictItemListValue!
}
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1621](https://github.com/strawberry-graphql/strawberry/pull/1621/)


0.95.1 - 2022-01-26
-------------------

Fix bug #1504 in the Pydantic integration, where it was impossible to define
both an input and output type based on the same Pydantic base class.

Contributed by [Matt Allen](https://github.com/Matt343) [PR #1592](https://github.com/strawberry-graphql/strawberry/pull/1592/)


0.95.0 - 2022-01-22
-------------------

Adds `to_pydantic` and `from_pydantic` type hints for IDE support.

Adds mypy extension support as well.

```python
from pydantic import BaseModel
import strawberry


class UserPydantic(BaseModel):
    age: int


@strawberry.experimental.pydantic.type(UserPydantic)
class UserStrawberry:
    age: strawberry.auto


reveal_type(UserStrawberry(age=123).to_pydantic())
```
Mypy will infer the type as "UserPydantic". Previously it would be "Any"

Contributed by [James Chua](https://github.com/thejaminator) [PR #1544](https://github.com/strawberry-graphql/strawberry/pull/1544/)


0.94.0 - 2022-01-18
-------------------

This release replaces `cached_property` with `backports.cached_property` to improve
the typing of the library.

Contributed by [Rishi Kumar Ray](https://github.com/RishiKumarRay) [PR #1582](https://github.com/strawberry-graphql/strawberry/pull/1582/)


0.93.23 - 2022-01-11
--------------------

Improve typing of `@strawberry.enum()` by:

1. Using a `TypeVar` bound on `EnumMeta` instead of `EnumMeta`, which allows
   type-checkers (like pyright) to detect the fields of the enum being
   decorated. For example, for the following enum:

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"
```

Prior to this change, pyright would complain if you tried to access
`IceCreamFlavour.VANILLA`, since the type information of `IceCreamFlavour` was
being erased by the `EnumMeta` typing .

2. Overloading it so that type-checkers (like pyright) knows in what cases it
   returns a decorator (when it's called with keyword arguments, e.g.
   `@strawberry.enum(name="IceCreamFlavor")`), versus when it returns the
   original enum type (without keyword arguments.

Contributed by [Tim Joseph Dumol](https://github.com/TimDumol) [PR #1568](https://github.com/strawberry-graphql/strawberry/pull/1568/)


0.93.22 - 2022-01-09
--------------------

This release adds `load_many` to `DataLoader`.

Contributed by [Silas Sewell](https://github.com/silas) [PR #1528](https://github.com/strawberry-graphql/strawberry/pull/1528/)


0.93.21 - 2022-01-07
--------------------

This release adds `deprecation_reason` support to arguments and mutations.

Contributed by [Silas Sewell](https://github.com/silas) [PR #1527](https://github.com/strawberry-graphql/strawberry/pull/1527/)


0.93.20 - 2022-01-07
--------------------

This release checks for AutoFieldsNotInBaseModelError when converting from pydantic models.
 It is raised when strawberry.auto is used, but the pydantic model does not have
the particular field defined.

```python
class User(BaseModel):
    age: int


@strawberry.experimental.pydantic.type(User)
class UserType:
    age: strawberry.auto
    password: strawberry.auto
```

Previously no errors would be raised, and the password field would not appear on graphql schema.
Such mistakes could be common during refactoring. Now, AutoFieldsNotInBaseModelError is raised.

Contributed by [James Chua](https://github.com/thejaminator) [PR #1551](https://github.com/strawberry-graphql/strawberry/pull/1551/)


0.93.19 - 2022-01-06
--------------------

Fixes TypeError when converting a pydantic BaseModel with NewType field

Contributed by [James Chua](https://github.com/thejaminator) [PR #1547](https://github.com/strawberry-graphql/strawberry/pull/1547/)


0.93.18 - 2022-01-05
--------------------

This release allows setting http headers and custom http status codes with FastAPI GraphQLRouter.

Contributed by [David Němec](https://github.com/davidnemec) [PR #1537](https://github.com/strawberry-graphql/strawberry/pull/1537/)


0.93.17 - 2022-01-05
--------------------

Fix compatibility with Sanic 21.12

Contributed by [Artjoms Iskovs](https://github.com/mildbyte) [PR #1520](https://github.com/strawberry-graphql/strawberry/pull/1520/)


0.93.16 - 2022-01-04
--------------------

Add support for piping `StrawberryUnion` and `None` when annotating types.

For example:
```python
@strawberry.type
class Cat:
    name: str


@strawberry.type
class Dog:
    name: str


Animal = strawberry.union("Animal", (Cat, Dog))


@strawberry.type
class Query:
    animal: Animal | None  # This line no longer triggers a TypeError
```

Contributed by [Yossi Rozantsev](https://github.com/Apakottur) [PR #1540](https://github.com/strawberry-graphql/strawberry/pull/1540/)


0.93.15 - 2022-01-04
--------------------

This release fixes the conversion of pydantic models with a default_factory
field.

Contributed by [James Chua](https://github.com/thejaminator) [PR #1538](https://github.com/strawberry-graphql/strawberry/pull/1538/)


0.93.14 - 2022-01-03
--------------------

This release allows conversion of pydantic models with mutable default fields into strawberry types.
Also fixes bug when converting a pydantic model field with default_factory. Previously it would raise an exception when fields with a default_factory were declared before fields without defaults.

Contributed by [James Chua](https://github.com/thejaminator) [PR #1491](https://github.com/strawberry-graphql/strawberry/pull/1491/)


0.93.13 - 2021-12-25
--------------------

This release updates the Decimal and UUID scalar parsers to exclude the original_error exception and format the error message similar to other builtin scalars.

Contributed by [Silas Sewell](https://github.com/silas) [PR #1507](https://github.com/strawberry-graphql/strawberry/pull/1507/)


0.93.12 - 2021-12-24
--------------------

Fix mypy plugin crushes when _get_type_for_expr is used on var nodes

Contributed by [Andrii Kohut](https://github.com/andriykohut) [PR #1513](https://github.com/strawberry-graphql/strawberry/pull/1513/)


0.93.11 - 2021-12-24
--------------------

This release fixes a bug in the annotation parser that prevents using strict typinh for Optional arguments which have their default set to UNSET.

Contributed by [Sarah Henkens](https://github.com/sarahhenkens) [PR #1467](https://github.com/strawberry-graphql/strawberry/pull/1467/)


0.93.10 - 2021-12-21
--------------------

This release adds support for mypy 0.920.

Contributed by [Yossi Rozantsev](https://github.com/Apakottur) [PR #1503](https://github.com/strawberry-graphql/strawberry/pull/1503/)


0.93.9 - 2021-12-21
-------------------

This releases fixes a bug with the opentracing extension
where the tracer wasn't replacing the field name correctly.

0.93.8 - 2021-12-20
-------------------

This release modifies the internal utility function `await_maybe` towards updating mypy to 0.920.

Contributed by [Yossi Rozantsev](https://github.com/Apakottur) [PR #1505](https://github.com/strawberry-graphql/strawberry/pull/1505/)


0.93.7 - 2021-12-18
-------------------

Change `context_getter` in `strawberry.fastapi.GraphQLRouter` to merge, rather than overwrite, default and custom getters.

This mean now you can always access the `request` instance from `info.context`, even when using
a custom context getter.

Contributed by [Tommy Smith](https://github.com/tsmith023) [PR #1494](https://github.com/strawberry-graphql/strawberry/pull/1494/)


0.93.6 - 2021-12-18
-------------------

This release changes when we fetch the event loop in dataloaders
to prevent using the wrong event loop in some occasions.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1498](https://github.com/strawberry-graphql/strawberry/pull/1498/)


0.93.5 - 2021-12-16
-------------------

This release fixes an issue that prevented from lazily importing
enum types using LazyType.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1501](https://github.com/strawberry-graphql/strawberry/pull/1501/)


0.93.4 - 2021-12-10
-------------------

This release allows running strawberry as a script, for example, you can start the debug server with the following command:

```shell
python -m strawberry server schema
```

Contributed by [YogiLiu](https://github.com/YogiLiu) [PR #1481](https://github.com/strawberry-graphql/strawberry/pull/1481/)


0.93.3 - 2021-12-08
-------------------

This release adds support for uvicorn 0.16

Contributed by [dependabot](https://github.com/dependabot) [PR #1487](https://github.com/strawberry-graphql/strawberry/pull/1487/)


0.93.2 - 2021-12-08
-------------------

This fixes the previous release that introduced a direct dependency on Django.

Contributed by [Guillaume Andreu Sabater](https://github.com/g-as) [PR #1489](https://github.com/strawberry-graphql/strawberry/pull/1489/)


0.93.1 - 2021-12-08
-------------------

This release adds support for Django 4.0

Contributed by [Guillaume Andreu Sabater](https://github.com/g-as) [PR #1484](https://github.com/strawberry-graphql/strawberry/pull/1484/)


0.93.0 - 2021-12-07
-------------------

This release `operation_type` to the `ExecutionContext` type that is available
in extensions. It also gets the `operation_name` from the query if one isn't
provided by the client.

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1286](https://github.com/strawberry-graphql/strawberry/pull/1286/)


0.92.2 - 2021-12-06
-------------------

This release adds support for passing `json_encoder` and `json_dumps_params` to Django [`JsonResponse`](https://docs.djangoproject.com/en/stable/ref/request-response/#jsonresponse-objects) via a view.


```python
from json import JSONEncoder

from django.urls import path
from strawberry.django.views import AsyncGraphQLView

from .schema import schema

# Pass the JSON params to `.as_view`
urlpatterns = [
    path(
        "graphql",
        AsyncGraphQLView.as_view(
            schema=schema,
            json_encoder=JSONEncoder,
            json_dumps_params={"separators": (",", ":")},
        ),
    ),
]


# … or set them in a custom view
class CustomAsyncGraphQLView(AsyncGraphQLView):
    json_encoder = JSONEncoder
    json_dumps_params = {"separators": (",", ":")}
```

Contributed by [Illia Volochii](https://github.com/illia-v) [PR #1472](https://github.com/strawberry-graphql/strawberry/pull/1472/)


0.92.1 - 2021-12-04
-------------------

Fix cross-module type resolving for fields and resolvers

The following two issues are now fixed:

- A field with a generic (typeless) resolver looks up the
  type relative to the resolver and not the class the field is
  defined in. (#1448)

- When inheriting fields from another class the origin of the
  fields are set to the inheriting class and not the class the
  field is defined in.

Both these issues could lead to a rather undescriptive error message:

> TypeError: (...) fields cannot be resolved. Unexpected type 'None'

Contributed by [Michael P. Jung](https://github.com/bikeshedder) [PR #1449](https://github.com/strawberry-graphql/strawberry/pull/1449/)


0.92.0 - 2021-12-04
-------------------

This releases fixes an issue where you were not allowed
to return a non-strawberry type for fields that return
an interface. Now this works as long as each type
implementing the interface implements an `is_type_of`
classmethod. Previous automatic duck typing on types
that implement an interface now requires explicit
resolution using this classmethod.

Contributed by [Etty](https://github.com/estyxx) [PR #1299](https://github.com/strawberry-graphql/strawberry/pull/1299/)


0.91.0 - 2021-12-04
-------------------

This release adds a `GraphQLTestClient`. It hides the http request's details and asserts that there are no errors in the response (you can always disable this behavior by passing `asserts_errors=False`). This makes it easier to test queries and makes your tests cleaner.

If you are using `pytest` you can add a fixture in `conftest.py`

```python
import pytest

from django.test.client import Client

from strawberry.django.test import GraphQLTestClient


@pytest.fixture
def graphql_client():
    yield GraphQLTestClient(Client())
```

And use it everywere in your test methods

```python
def test_strawberry(graphql_client):
    query = """
        query Hi($name: String!) {
            hi(name: $name)
        }
    """

    result = graphql_client.query(query, variables={"name": "Marcotte"})

    assert result.data == {"hi": "Hi Marcotte!"}
```

It can be used to test the file uploads as well

```python
from django.core.files.uploadedfile import SimpleUploadedFile


def test_upload(graphql_client):
    f = SimpleUploadedFile("file.txt", b"strawberry")
    query = """
        mutation($textFile: Upload!) {
            readText(textFile: $textFile)
        }
    """

    response = graphql_client.query(
        query=query,
        variables={"textFile": None},
        files={"textFile": f},
    )

    assert response.data["readText"] == "strawberry"
```

Contributed by [Etty](https://github.com/estyxx) [PR #1225](https://github.com/strawberry-graphql/strawberry/pull/1225/)


0.90.3 - 2021-12-02
-------------------

This release fixes an issue that prevented using enums as
arguments for generic types inside unions.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1463](https://github.com/strawberry-graphql/strawberry/pull/1463/)


0.90.2 - 2021-11-28
-------------------

This release fixes the message of `InvalidFieldArgument` to properly show the field's name in the error message.

Contributed by [Etty](https://github.com/estyxx) [PR #1322](https://github.com/strawberry-graphql/strawberry/pull/1322/)


0.90.1 - 2021-11-27
-------------------

This release fixes an issue that prevented using `classmethod`s and `staticmethod`s as resolvers

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    @staticmethod
    def static_text() -> str:
        return "Strawberry"

    @strawberry.field
    @classmethod
    def class_name(cls) -> str:
        return cls.__name__
```

Contributed by [Illia Volochii](https://github.com/illia-v) [PR #1430](https://github.com/strawberry-graphql/strawberry/pull/1430/)


0.90.0 - 2021-11-26
-------------------

This release improves type checking support for `strawberry.union` and now allows
to use unions without any type issue, like so:

```python
@strawberry.type
class User:
    name: str


@strawberry.type
class Error:
    message: str


UserOrError = strawberry.union("UserOrError", (User, Error))

x: UserOrError = User(name="Patrick")
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1438](https://github.com/strawberry-graphql/strawberry/pull/1438/)


0.89.2 - 2021-11-26
-------------------

Fix init of Strawberry types from pydantic by skipping fields that have resolvers.

Contributed by [Nina](https://github.com/nina-j) [PR #1451](https://github.com/strawberry-graphql/strawberry/pull/1451/)


0.89.1 - 2021-11-25
-------------------

This release fixes an issubclass test failing for `Literal`s in the experimental `pydantic` integration.

Contributed by [Nina](https://github.com/nina-j) [PR #1445](https://github.com/strawberry-graphql/strawberry/pull/1445/)


0.89.0 - 2021-11-24
-------------------

This release changes how `strawberry.Private` is implemented to
improve support for type checkers.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1437](https://github.com/strawberry-graphql/strawberry/pull/1437/)


0.88.0 - 2021-11-24
-------------------

This release adds support for AWS Chalice. A framework for deploying serverless applications using AWS.

A view for aws chalice has been added to the strawberry codebase.
This view embedded in a chalice app allows anyone to get a GraphQL API working and hosted on AWS in minutes using a serverless architecture.

Contributed by [Mark Sheehan](https://github.com/mcsheehan) [PR #923](https://github.com/strawberry-graphql/strawberry/pull/923/)


0.87.3 - 2021-11-23
-------------------

This release fixes the naming generation of generics when
passing a generic type to another generic, like so:

```python
@strawberry.type
class Edge(Generic[T]):
    node: T


@strawberry.type
class Connection(Generic[T]):
    edges: List[T]


Connection[Edge[int]]
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1436](https://github.com/strawberry-graphql/strawberry/pull/1436/)


0.87.2 - 2021-11-19
-------------------

This releases updates the `typing_extension` dependency to latest version.

Contributed by [dependabot](https://github.com/dependabot) [PR #1417](https://github.com/strawberry-graphql/strawberry/pull/1417/)


0.87.1 - 2021-11-15
-------------------

This release renames an internal exception from `NotAnEnum` to `ObjectIsNotAnEnumError`.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1317](https://github.com/strawberry-graphql/strawberry/pull/1317/)


0.87.0 - 2021-11-15
-------------------

This release changes how we handle GraphQL names. It also introduces a new
configuration option called `name_converter`. This option allows you to specify
a custom `NameConverter` to be used when generating GraphQL names.

This is currently not documented because the API will change slightly in future
as we are working on renaming internal types.

This release also fixes an issue when creating concrete types from generic when
passing list objects.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1394](https://github.com/strawberry-graphql/strawberry/pull/1394/)


0.86.1 - 2021-11-12
-------------------

This release fixes our MyPy plugin and re-adds support
for typechecking classes created with the apollo federation decorator.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1414](https://github.com/strawberry-graphql/strawberry/pull/1414/)


0.86.0 - 2021-11-12
-------------------

Add `on_executing_*` hooks to extensions to allow you to override the execution phase of a GraphQL operation.

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1400](https://github.com/strawberry-graphql/strawberry/pull/1400/)


0.85.1 - 2021-10-26
-------------------

This release fixes an issue with schema directives not
being printed correctly.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1376](https://github.com/strawberry-graphql/strawberry/pull/1376/)


0.85.0 - 2021-10-23
-------------------

This release introduces initial support for schema directives and
updates the federation support to use that.

Full support will be implemented in future releases.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #815](https://github.com/strawberry-graphql/strawberry/pull/815/)


0.84.4 - 2021-10-23
-------------------

Field definition uses output of `default_factory` as the GraphQL `default_value`.
```python
a_field: list[str] = strawberry.field(default_factory=list)
```
```graphql
aField: [String!]! = []
```

Contributed by [A. Coady](https://github.com/coady) [PR #1371](https://github.com/strawberry-graphql/strawberry/pull/1371/)


0.84.3 - 2021-10-19
-------------------

This release fixed the typing support for Pyright.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1363](https://github.com/strawberry-graphql/strawberry/pull/1363/)


0.84.2 - 2021-10-17
-------------------

This release adds an extra dependency for FastAPI to prevent
it being downloaded even when not needed.

To install Strawberry with FastAPI support you can do:

```
pip install 'strawberry-graphql[fastapi]'
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1366](https://github.com/strawberry-graphql/strawberry/pull/1366/)


0.84.1 - 2021-10-17
-------------------

This release fixes the `merge_types` type signature.

Contributed by [Guillaume Andreu Sabater](https://github.com/g-as) [PR #1348](https://github.com/strawberry-graphql/strawberry/pull/1348/)


0.84.0 - 2021-10-16
-------------------

This release adds support for FastAPI integration using APIRouter.

```python
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

Contributed by [Jiří Bireš](https://github.com/jiribires) [PR #1291](https://github.com/strawberry-graphql/strawberry/pull/1291/)


0.83.6 - 2021-10-16
-------------------

Improve help texts for CLI to work better on ZSH.

Contributed by [Magnus Markling](https://github.com/memark) [PR #1360](https://github.com/strawberry-graphql/strawberry/pull/1360/)


0.83.5 - 2021-10-16
-------------------

Errors encountered in subscriptions will now be logged to the `strawberry.execution` logger as errors encountered in Queries and Mutations are. <3

Contributed by [Michael Ossareh](https://github.com/ossareh) [PR #1316](https://github.com/strawberry-graphql/strawberry/pull/1316/)


0.83.4 - 2021-10-13
-------------------

Add logic to convert arguments of type LazyType.

Contributed by [Luke Murray](https://github.com/lukesmurray) [PR #1350](https://github.com/strawberry-graphql/strawberry/pull/1350/)


0.83.3 - 2021-10-13
-------------------

This release fixes a bug where passing scalars in the `scalar_overrides`
parameter wasn't being applied consistently.

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1212](https://github.com/strawberry-graphql/strawberry/pull/1212/)


0.83.2 - 2021-10-13
-------------------

Pydantic fields' `description` are now copied to the GraphQL schema

```python
import pydantic
import strawberry


class UserModel(pydantic.BaseModel):
    age: str = pydantic.Field(..., description="Description")


@strawberry.experimental.pydantic.type(UserModel)
class User:
    age: strawberry.auto
```

```
type User {
  """Description"""
  age: String!
}
```

Contributed by [Guillaume Andreu Sabater](https://github.com/g-as) [PR #1332](https://github.com/strawberry-graphql/strawberry/pull/1332/)


0.83.1 - 2021-10-12
-------------------

We now run our tests against Windows during CI!

Contributed by [Michael Ossareh](https://github.com/ossareh) [PR #1321](https://github.com/strawberry-graphql/strawberry/pull/1321/)


0.83.0 - 2021-10-12
-------------------

Add a shortcut to merge queries, mutations. E.g.:

```python
import strawberry
from strawberry.tools import merge_types


@strawberry.type
class QueryA: ...


@strawberry.type
class QueryB: ...


ComboQuery = merge_types("ComboQuery", (QueryB, QueryA))
schema = strawberry.Schema(query=ComboQuery)
```

Contributed by [Alexandru Mărășteanu](https://github.com/alexei) [PR #1273](https://github.com/strawberry-graphql/strawberry/pull/1273/)


0.82.2 - 2021-10-12
-------------------

Makes the GraphQLSchema instance accessible from resolvers via the `info` parameter.

Contributed by [Aryan Iyappan](https://github.com/codebyaryan) [PR #1311](https://github.com/strawberry-graphql/strawberry/pull/1311/)


0.82.1 - 2021-10-11
-------------------

Fix bug where errors thrown in the on_parse_* extension hooks were being
swallowed instead of being propagated.

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1324](https://github.com/strawberry-graphql/strawberry/pull/1324/)


0.82.0 - 2021-10-11
-------------------

Adds support for the `auto` type annotation described in #1192 to the Pydantic
integration, which allows a user to define the list of fields without having to
re-specify the type themselves. This gives better editor and type checker
support. If you want to expose every field you can instead pass
`all_fields=True` to the decorators and leave the body empty.

```python
import pydantic
import strawberry
from strawberry.experimental.pydantic import auto


class User(pydantic.BaseModel):
    age: int
    password: str


@strawberry.experimental.pydantic.type(User)
class UserType:
    age: auto
    password: auto
```

Contributed by [Matt Allen](https://github.com/Matt343) [PR #1280](https://github.com/strawberry-graphql/strawberry/pull/1280/)


0.81.0 - 2021-10-04
-------------------

This release adds a safety check on `strawberry.type`, `strawberry.input` and
`strawberry.interface` decorators. When you try to use them with an object that is not a
class, you will get a nice error message:
`strawberry.type can only be used with classes`

Contributed by [dependabot](https://github.com/dependabot) [PR #1278](https://github.com/strawberry-graphql/strawberry/pull/1278/)


0.80.2 - 2021-10-01
-------------------

Add `Starlette` to the integrations section on the documentation.

Contributed by [Marcelo Trylesinski](https://github.com/Kludex) [PR #1287](https://github.com/strawberry-graphql/strawberry/pull/1287/)


0.80.1 - 2021-10-01
-------------------

This release add support for the upcoming python 3.10 and it adds support
for the new union syntax, allowing to declare unions like this:

```python
import strawberry


@strawberry.type
class User:
    name: str


@strawberry.type
class Error:
    code: str


@strawberry.type
class Query:
    find_user: User | Error
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #719](https://github.com/strawberry-graphql/strawberry/pull/719/)


0.80.0 - 2021-09-30
-------------------

This release adds support for the `graphql-transport-ws` GraphQL over WebSocket
protocol. Previously Strawberry only supported the legacy `graphql-ws` protocol.

Developers can decide which protocols they want to accept. The following example shows
how to do so using the ASGI integration. By default, both protocols are accepted.
Take a look at our GraphQL subscription documentation to learn more.

```python
from strawberry.asgi import GraphQL
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from api.schema import schema


app = GraphQL(schema, subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])
```

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1256](https://github.com/strawberry-graphql/strawberry/pull/1256/)


0.79.0 - 2021-09-29
-------------------

Nests the resolver under the correct span; prior to this change your span would have looked something like:

```
GraphQL Query
  GraphQL Parsing
  GraphQL Validation
  my_resolver
  my_span_of_interest #1
    my_sub_span_of_interest #2
```

After this change you'll have:

```
GraphQL Query
  GraphQL Parsing
  GraphQL Validation
  GraphQL Resolving: my_resolver
    my_span_of_interest #1
      my_sub_span_of_interest #2
```

Contributed by [Michael Ossareh](https://github.com/ossareh) [PR #1281](https://github.com/strawberry-graphql/strawberry/pull/1281/)


0.78.2 - 2021-09-27
-------------------

Enhances strawberry.extensions.tracing.opentelemetry to include spans for the Parsing and Validation phases of request handling. These occur before your resovler is called, so now you can see how much time those phases take up!

Contributed by [Michael Ossareh](https://github.com/ossareh) [PR #1274](https://github.com/strawberry-graphql/strawberry/pull/1274/)


0.78.1 - 2021-09-26
-------------------

Fix `extensions` argument type definition on `strawberry.Schema`

Contributed by [Guillaume Andreu Sabater](https://github.com/g-as) [PR #1276](https://github.com/strawberry-graphql/strawberry/pull/1276/)


0.78.0 - 2021-09-22
-------------------

This release introduces some brand new extensions to help improve the
performance of your GraphQL server:

* `ParserCache` - Cache the parsing of a query in memory
* `ValidationCache` - Cache the validation step of execution

For complicated queries these 2 extensions can improve performance by over 50%!

Example:

```python
import strawberry
from strawberry.extensions import ParserCache, ValidationCache

schema = strawberry.Schema(
    Query,
    extensions=[
        ParserCache(),
        ValidationCache(),
    ],
)
```

This release also removes the `validate_queries` and `validation_rules`
parameters on the `schema.execute*` methods in favour of using the
`DisableValidation` and `AddValidationRule` extensions.

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1196](https://github.com/strawberry-graphql/strawberry/pull/1196/)


0.77.12 - 2021-09-20
--------------------

This release adds support for Sanic v21

Contributed by [dependabot](https://github.com/dependabot) [PR #1105](https://github.com/strawberry-graphql/strawberry/pull/1105/)


0.77.11 - 2021-09-19
--------------------

Fixes returning "500 Internal Server Error" responses to requests with malformed json when running with ASGI integration.

Contributed by [Olesia Grydzhuk](https://github.com/Zlira) [PR #1260](https://github.com/strawberry-graphql/strawberry/pull/1260/)


0.77.10 - 2021-09-16
--------------------

This release adds `python_name` to the `Info` type.

Contributed by [Joe Freeman](https://github.com/joefreeman) [PR #1257](https://github.com/strawberry-graphql/strawberry/pull/1257/)


0.77.9 - 2021-09-16
-------------------

Fix the Pydantic conversion method for Enum values, and add a mechanism to specify an interface type when converting from Pydantic. The Pydantic interface is really a base dataclass for the subclasses to extend. When you do the conversion, you have to use `strawberry.experimental.pydantic.interface` to let us know that this type is an interface. You also have to use your converted interface type as the base class for the sub types as normal.

Contributed by [Matt Allen](https://github.com/Matt343) [PR #1241](https://github.com/strawberry-graphql/strawberry/pull/1241/)


0.77.8 - 2021-09-14
-------------------

Fixes a bug with the `selected_fields` property on `info` when an operation
variable is not defined.

Issue [#1248](https://github.com/strawberry-graphql/strawberry/issues/1248).

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1249](https://github.com/strawberry-graphql/strawberry/pull/1249/)


0.77.7 - 2021-09-14
-------------------

Fix issues ([#1158][issue1158] and [#1104][issue1104]) where Generics using LazyTypes
and Enums would not be properly resolved

These now function as expected:

# Enum

```python
T = TypeVar("T")


@strawberry.enum
class VehicleMake(Enum):
    FORD = "ford"
    TOYOTA = "toyota"
    HONDA = "honda"


@strawberry.type
class GenericForEnum(Generic[T]):
    generic_slot: T


@strawberry.type
class SomeType:
    field: GenericForEnum[VehicleMake]
```

# LazyType

`another_file.py`
```python
@strawberry.type
class TypeFromAnotherFile:
    something: bool
```

`this_file.py`
```python
T = TypeVar("T")


@strawberry.type
class GenericType(Generic[T]):
    item: T


@strawberry.type
class RealType:
    lazy: GenericType[LazyType["TypeFromAnotherFile", "another_file.py"]]
```

[issue1104]: https://github.com/strawberry-graphql/strawberry/issues/1104
[issue1158]: https://github.com/strawberry-graphql/strawberry/issues/1158

Contributed by [ignormies](https://github.com/BryceBeagle) [PR #1235](https://github.com/strawberry-graphql/strawberry/pull/1235/)


0.77.6 - 2021-09-13
-------------------

This release adds fragment and input variable information to the
`selected_fields` attribute on the `Info` object.

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1213](https://github.com/strawberry-graphql/strawberry/pull/1213/)


0.77.5 - 2021-09-11
-------------------

Fixes a bug in the Pydantic conversion code around `Union` values.

Contributed by [Matt Allen](https://github.com/Matt343) [PR #1231](https://github.com/strawberry-graphql/strawberry/pull/1231/)


0.77.4 - 2021-09-11
-------------------

Fixes a bug in the `export-schema` command around the handling of local modules.

Contributed by [Matt Allen](https://github.com/Matt343) [PR #1233](https://github.com/strawberry-graphql/strawberry/pull/1233/)


0.77.3 - 2021-09-10
-------------------

Fixes a bug in the Pydantic conversion code around complex `Optional` values.

Contributed by [Matt Allen](https://github.com/Matt343) [PR #1229](https://github.com/strawberry-graphql/strawberry/pull/1229/)


0.77.2 - 2021-09-10
-------------------

This release adds a new exception called `InvalidFieldArgument` which is raised when a Union or Interface is used as an argument type.
For example this will raise an exception:
```python
import strawberry


@strawberry.type
class Noun:
    text: str


@strawberry.type
class Verb:
    text: str


Word = strawberry.union("Word", types=(Noun, Verb))


@strawberry.field
def add_word(word: Word) -> bool: ...
```

Contributed by [Mohammad Hossein Yazdani](https://github.com/MAM-SYS) [PR #1222](https://github.com/strawberry-graphql/strawberry/pull/1222/)


0.77.1 - 2021-09-10
-------------------

Fix type resolution when inheriting from types from another module using deferred annotations.

Contributed by [Daniel Bowring](https://github.com/dbowring) [PR #1010](https://github.com/strawberry-graphql/strawberry/pull/1010/)


0.77.0 - 2021-09-10
-------------------

This release adds support for Pyright and Pylance, improving the
integration with Visual Studio Code!

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #922](https://github.com/strawberry-graphql/strawberry/pull/922/)


0.76.1 - 2021-09-09
-------------------

Change the version constraint of opentelemetry-sdk and opentelemetry-api to <2

Contributed by [Michael Ossareh](https://github.com/ossareh) [PR #1226](https://github.com/strawberry-graphql/strawberry/pull/1226/)


0.76.0 - 2021-09-06
-------------------

This release adds support for enabling subscriptions in GraphiQL
on Django by setting a flag `subscriptions_enabled` on the BaseView class.
```python
from strawberry.django.views import AsyncGraphQLView

from .schema import schema

urlpatterns = [
    path(
        "graphql",
        AsyncGraphQLView.as_view(
            schema=schema, graphiql=True, subscriptions_enabled=True
        ),
    )
]
```

Contributed by [lijok](https://github.com/lijok) [PR #1215](https://github.com/strawberry-graphql/strawberry/pull/1215/)


0.75.1 - 2021-09-03
-------------------

This release fixes an issue with the MyPy plugin that prevented using
TextChoices from django in `strawberry.enum`.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1202](https://github.com/strawberry-graphql/strawberry/pull/1202/)


0.75.0 - 2021-09-01
-------------------

This release improves how we deal with custom scalars. Instead of being global
they are now scoped to the schema. This allows you to have multiple schemas in
the same project with different scalars.

Also you can now override the built in scalars with your own custom
implementation. Out of the box Strawberry provides you with custom scalars for
common Python types like `datetime` and `Decimal`. If you require a custom
implementation of one of these built in scalars you can now pass a map of
overrides to your schema:

```python
from datetime import datetime, timezone
import strawberry

EpochDateTime = strawberry.scalar(
    datetime,
    serialize=lambda value: int(value.timestamp()),
    parse_value=lambda value: datetime.fromtimestamp(int(value), timezone.utc),
)


@strawberry.type
class Query:
    @strawberry.field
    def current_time(self) -> datetime:
        return datetime.now()


schema = strawberry.Schema(
    Query,
    scalar_overrides={
        datetime: EpochDateTime,
    },
)
result = schema.execute_sync("{ currentTime }")
assert result.data == {"currentTime": 1628683200}
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1147](https://github.com/strawberry-graphql/strawberry/pull/1147/)


0.74.1 - 2021-08-27
-------------------

This release allows to install Strawberry along side `click` version 8.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1181](https://github.com/strawberry-graphql/strawberry/pull/1181/)


0.74.0 - 2021-08-27
-------------------

This release add full support for async directives and fixes and issue when
using directives and async extensions.

```python
@strawberry.type
class Query:
    name: str = "Banana"


@strawberry.directive(
    locations=[DirectiveLocation.FIELD], description="Make string uppercase"
)
async def uppercase(value: str):
    return value.upper()


schema = strawberry.Schema(query=Query, directives=[uppercase])
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1179](https://github.com/strawberry-graphql/strawberry/pull/1179/)


0.73.9 - 2021-08-26
-------------------

Fix issue where `strawberry.Private` fields on converted Pydantic types were not added to the resulting dataclass.

Contributed by [Paul Sud](https://github.com/paul-sud) [PR #1173](https://github.com/strawberry-graphql/strawberry/pull/1173/)


0.73.8 - 2021-08-26
-------------------

This releases fixes a MyPy issue that prevented from using types created with
`create_type` as base classes. This is now allowed and doesn't throw any error:

```python
import strawberry
from strawberry.tools import create_type


@strawberry.field
def name() -> str:
    return "foo"


MyType = create_type("MyType", [name])


class Query(MyType): ...
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1175](https://github.com/strawberry-graphql/strawberry/pull/1175/)


0.73.7 - 2021-08-25
-------------------

This release fixes an import error when trying to import `create_type` without having `opentelemetry` installed.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1171](https://github.com/strawberry-graphql/strawberry/pull/1171/)


0.73.6 - 2021-08-24
-------------------

This release adds support for the latest version of the optional opentelemetry dependency.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1170](https://github.com/strawberry-graphql/strawberry/pull/1170/)


0.73.5 - 2021-08-24
-------------------

This release adds support for the latest version of the optional opentelemetry dependency.

Contributed by [Joe Freeman](https://github.com/joefreeman) [PR #1169](https://github.com/strawberry-graphql/strawberry/pull/1169/)


0.73.4 - 2021-08-24
-------------------

This release allows background tasks to be set with the ASGI integration. Tasks can be set on the response in the context, and will then get run after the query result is returned.

```python
from starlette.background import BackgroundTask


@strawberry.mutation
def create_flavour(self, info: strawberry.Info) -> str:
    info.context["response"].background = BackgroundTask(...)
```

Contributed by [Joe Freeman](https://github.com/joefreeman) [PR #1168](https://github.com/strawberry-graphql/strawberry/pull/1168/)


0.73.3 - 2021-08-24
-------------------

This release caches attributes on the `Info` type which aren't delegated to the core info object.

Contributed by [A. Coady](https://github.com/coady) [PR #1167](https://github.com/strawberry-graphql/strawberry/pull/1167/)


0.73.2 - 2021-08-23
-------------------

This releases fixes an issue where you were not allowed
to use duck typing and return a different type that the
type declared on the field when the type was implementing
an interface. Now this works as long as you return a type
that has the same shape as the field type.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1150](https://github.com/strawberry-graphql/strawberry/pull/1150/)


0.73.1 - 2021-08-23
-------------------

This release improves execution performance significantly by lazy loading
attributes on the `Info` type 🏎

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1165](https://github.com/strawberry-graphql/strawberry/pull/1165/)


0.73.0 - 2021-08-22
-------------------

This release adds support for asynchronous hooks to the Strawberry extension-system.
All available hooks can now be implemented either synchronously or asynchronously.

It's also possible to mix both synchronous and asynchronous hooks within one extension.


```python
from strawberry.extensions import Extension


class MyExtension(Extension):
    async def on_request_start(self):
        print("GraphQL request start")

    def on_request_end(self):
        print("GraphQL request end")
```

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1142](https://github.com/strawberry-graphql/strawberry/pull/1142/)


0.72.3 - 2021-08-22
-------------------

This release refactors the reload feature of the built-in debug server. The refactor
made the debug server more responsive and allowed us to remove `hupper` from the
dependencies.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1114](https://github.com/strawberry-graphql/strawberry/pull/1114/)


0.72.2 - 2021-08-22
-------------------

This releases pins graphql-core to only accept patch versions in order to prevent breaking changes since graphql-core doesn't properly follow semantic versioning.

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1162](https://github.com/strawberry-graphql/strawberry/pull/1162/)


0.72.1 - 2021-08-18
-------------------

This release improves the default logging format for errors to include more information about the errors. For example it will show were an error was originated in a request:

```
GraphQL request:2:5
1 | query {
2 |     example
  |     ^
3 | }
```

Contributed by [Ivan Gonzalez](https://github.com/scratchmex) [PR #1152](https://github.com/strawberry-graphql/strawberry/pull/1152/)


0.72.0 - 2021-08-18
-------------------

This release adds support for asynchronous permission classes. The only difference to
their synchronous counterpart is that the `has_permission` method is asynchronous.

```python
from strawberry.permission import BasePermission


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    async def has_permission(self, source, info, **kwargs):
        return True
```

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1125](https://github.com/strawberry-graphql/strawberry/pull/1125/)


0.71.3 - 2021-08-11
-------------------

Get a field resolver correctly when extending from a pydantic model

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1116](https://github.com/strawberry-graphql/strawberry/pull/1116/)


0.71.2 - 2021-08-10
-------------------

This release adds `asgi` as an extra dependencies group for Strawberry. Now
you can install the required dependencies needed to use Strawberry with
ASGI by running:

```
pip install 'strawberry[asgi]'
```

Contributed by [A. Coady](https://github.com/coady) [PR #1036](https://github.com/strawberry-graphql/strawberry/pull/1036/)


0.71.1 - 2021-08-09
-------------------

This releases adds `selected_fields` on the `info` objects and it
allows to introspect the fields that have been selected in a GraphQL
operation.

This can become useful to run optimisation based on the queried fields.

Contributed by [A. Coady](https://github.com/coady) [PR #874](https://github.com/strawberry-graphql/strawberry/pull/874/)


0.71.0 - 2021-08-08
-------------------

This release adds a query depth limit validation rule so that you can guard
against malicious queries:

```python
import strawberry
from strawberry.schema import default_validation_rules
from strawberry.tools import depth_limit_validator


# Add the depth limit validator to the list of default validation rules
validation_rules = default_validation_rules + [depth_limit_validator(3)]

result = schema.execute_sync(
    """
    query MyQuery {
      user {
        pets {
          owner {
            pets {
              name
            }
          }
        }
      }
    }
    """,
    validation_rules=validation_rules,
)
assert len(result.errors) == 1
assert result.errors[0].message == "'MyQuery' exceeds maximum operation depth of 3"
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1021](https://github.com/strawberry-graphql/strawberry/pull/1021/)


0.70.4 - 2021-08-07
-------------------

Addition of `app.add_websocket_route("/subscriptions", graphql_app)` to FastAPI example docs

Contributed by [Anton Melser](https://github.com/AntonOfTheWoods) [PR #1103](https://github.com/strawberry-graphql/strawberry/pull/1103/)


0.70.3 - 2021-08-06
-------------------

This release changes how we map Pydantic fields to types
to allow using older version of Pydantic.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1071](https://github.com/strawberry-graphql/strawberry/pull/1071/)


0.70.2 - 2021-08-04
-------------------

This release makes the `strawberry server` command inform the user about missing
dependencies required by the builtin debug server.

Also `hupper` a package only used by said command has been made optional.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1107](https://github.com/strawberry-graphql/strawberry/pull/1107/)


0.70.1 - 2021-08-01
-------------------

Switch CDN used to load GraphQLi dependencies from jsdelivr.com to unpkg.com

Contributed by [Tim Savage](https://github.com/timsavage) [PR #1096](https://github.com/strawberry-graphql/strawberry/pull/1096/)


0.70.0 - 2021-07-23
-------------------

This release adds support for disabling auto camel casing. It
does so by introducing a new configuration parameter to the schema.

You can use it like so:

```python
@strawberry.type
class Query:
    example_field: str = "Example"


schema = strawberry.Schema(query=Query, config=StrawberryConfig(auto_camel_case=False))
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #798](https://github.com/strawberry-graphql/strawberry/pull/798/)


0.69.4 - 2021-07-23
-------------------

Fix for regression when defining inherited types with explicit fields.

Contributed by [A. Coady](https://github.com/coady) [PR #1076](https://github.com/strawberry-graphql/strawberry/pull/1076/)


0.69.3 - 2021-07-21
-------------------

This releases improves the MyPy plugin to be more forgiving of
settings like follow_imports = skip which would break the type checking.

This is a continuation of the previous release and fixes for type checking issues.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1078](https://github.com/strawberry-graphql/strawberry/pull/1078/)


0.69.2 - 2021-07-21
-------------------

This releases improves the MyPy plugin to be more forgiving of
settings like `follow_imports = skip` which would break the
type checking.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1077](https://github.com/strawberry-graphql/strawberry/pull/1077/)


0.69.1 - 2021-07-20
-------------------

This release removes a `TypeGuard` import to prevent errors
when using older versions of `typing_extensions`.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1074](https://github.com/strawberry-graphql/strawberry/pull/1074/)


0.69.0 - 2021-07-20
-------------------

Refactor of the library's typing internals. Previously, typing was handled
individually by fields, arguments, and objects with a hodgepodge of functions to tie it
together. This change creates a unified typing system that the object, fields, and
arguments each hook into.

Mainly replaces the attributes that were stored on StrawberryArgument and
StrawberryField with a hierarchy of StrawberryTypes.

Introduces `StrawberryAnnotation`, as well as `StrawberryType` and some subclasses,
including `StrawberryList`, `StrawberryOptional`, and `StrawberryTypeVar`.

This is a breaking change if you were calling the constructor for `StrawberryField`,
`StrawberryArgument`, etc. and using arguments such as `is_optional` or `child`.

`@strawberry.field` no longer takes an argument called `type_`. It instead takes a
`StrawberryAnnotation` called `type_annotation`.

Contributed by [ignormies](https://github.com/BryceBeagle) [PR #906](https://github.com/strawberry-graphql/strawberry/pull/906/)


0.68.4 - 2021-07-19
-------------------

This release fixes an issue with the federation printer that
prevented using federation directives with types that were
implementing interfaces.

This is now allowed:

```python
@strawberry.interface
class SomeInterface:
    id: strawberry.ID


@strawberry.federation.type(keys=["upc"], extend=True)
class Product(SomeInterface):
    upc: str = strawberry.federation.field(external=True)
```

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1068](https://github.com/strawberry-graphql/strawberry/pull/1068/)


0.68.3 - 2021-07-15
-------------------

This release changes our `graphiql.html` template to use a specific version of `js-cookie`
to prevent a JavaScript error, see:

https://github.com/js-cookie/js-cookie/issues/698

Contributed by [星](https://github.com/star2000) [PR #1062](https://github.com/strawberry-graphql/strawberry/pull/1062/)


0.68.2 - 2021-07-07
-------------------

This release fixes a regression that broke strawberry-graphql-django.

`Field.get_results` now always receives the `info` argument.

Contributed by [Lauri Hintsala](https://github.com/la4de) [PR #1047](https://github.com/strawberry-graphql/strawberry/pull/1047/)


0.68.1 - 2021-07-05
-------------------

This release only changes some internal code to make future improvements
easier.

Contributed by [Patrick Arminio](https://github.com/patrick91) [PR #1044](https://github.com/strawberry-graphql/strawberry/pull/1044/)


0.68.0 - 2021-07-03
-------------------

Matching the behaviour of `graphql-core`, passing an incorrect ISO string value for a Time, Date or DateTime scalar now raises a `GraphQLError` instead of the original parsing error.

The `GraphQLError` will include the error message raised by the string parser, e.g. `Value cannot represent a DateTime: "2021-13-01T09:00:00". month must be in 1..12`

0.67.1 - 2021-06-22
-------------------

Fixes [#1022](https://github.com/strawberry-graphql/strawberry/issues/1022) by making starlette an optional dependency.

Contributed by [Marcel Wiegand](https://github.com/mawiegand) [PR #1027](https://github.com/strawberry-graphql/strawberry/pull/1027/)


0.67.0 - 2021-06-17
-------------------

Add ability to specific the graphql name for a resolver argument. E.g.,

```python
from typing import Annotated
import strawberry


@strawberry.input
class HelloInput:
    name: str = "world"


@strawberry.type
class Query:
    @strawberry.field
    def hello(
        self, input_: Annotated[HelloInput, strawberry.argument(name="input")]
    ) -> str:
        return f"Hi {input_.name}"
```

Contributed by [Daniel Bowring](https://github.com/dbowring) [PR #1024](https://github.com/strawberry-graphql/strawberry/pull/1024/)


0.66.0 - 2021-06-15
-------------------

This release fixes a bug that was preventing the use of an enum member as the
default value for an argument.

For example:

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"
    PISTACHIO = "pistachio"


@strawberry.mutation
def create_flavour(self, flavour: IceCreamFlavour = IceCreamFlavour.STRAWBERRY) -> str:
    return f"{flavour.name}"
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #1015](https://github.com/strawberry-graphql/strawberry/pull/1015/)


0.65.5 - 2021-06-15
-------------------

This release reverts the changes made in v0.65.4 that caused an issue leading to
circular imports when using the `strawberry-graphql-django` extension package.

Contributed by [Lauri Hintsala](https://github.com/la4de) [PR #1019](https://github.com/strawberry-graphql/strawberry/pull/1019/)


0.65.4 - 2021-06-14
-------------------

This release fixes the IDE integration where package `strawberry.django` could not be find by some editors like vscode.

Contributed by [Lauri Hintsala](https://github.com/la4de) [PR #994](https://github.com/strawberry-graphql/strawberry/pull/994/)


0.65.3 - 2021-06-09
-------------------

This release fixes the ASGI subscription implementation by handling disconnecting clients properly.

Additionally, the ASGI implementation has been internally refactored to match the AIOHTTP implementation.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1002](https://github.com/strawberry-graphql/strawberry/pull/1002/)


0.65.2 - 2021-06-06
-------------------

This release fixes a bug in the subscription implementations that prevented clients
from selecting one of multiple subscription operations from a query. Client sent
messages like the following one are now handled as expected.

```json
{
  "type": "GQL_START",
  "id": "DEMO",
  "payload": {
    "query": "subscription Sub1 { sub1 } subscription Sub2 { sub2 }",
    "operationName": "Sub2"
  }
}
```

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #1000](https://github.com/strawberry-graphql/strawberry/pull/1000/)


0.65.1 - 2021-06-02
-------------------

This release fixes the upload of nested file lists. Among other use cases, having an
input type like shown below is now working properly.

```python
import typing
import strawberry
from strawberry.file_uploads import Upload


@strawberry.input
class FolderInput:
    files: typing.List[Upload]
```

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #989](https://github.com/strawberry-graphql/strawberry/pull/989/)


0.65.0 - 2021-06-01
-------------------

This release extends the file upload support of all integrations to support the upload
of file lists.

Here is an example how this would work with the ASGI integration.

```python
import typing
import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            content = (await file.read()).decode()
            contents.append(content)
        return contents
```

Check out the documentation to learn how the same can be done with other integrations.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #979](https://github.com/strawberry-graphql/strawberry/pull/979/)


0.64.5 - 2021-05-28
-------------------

This release fixes that AIOHTTP subscription requests were not properly separated.
This could lead to subscriptions terminating each other.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #970](https://github.com/strawberry-graphql/strawberry/pull/970/)


0.64.4 - 2021-05-28
-------------------

* Remove usages of `undefined` in favour of `UNSET`
* Change the signature of `StrawberryField` to make it easier to instantiate
directly. Also change `default_value` argument to `default`
* Rename `default_value` to `default` in `StrawberryArgument`

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #916](https://github.com/strawberry-graphql/strawberry/pull/916/)


0.64.3 - 2021-05-26
-------------------

This release integrates the `strawberry-graphql-django` package into Strawberry
core so that it's possible to use the Django extension package directly via the
`strawberry.django` namespace.

You still need to install `strawberry-graphql-django` if you want to use the
extended Django support.

See: https://github.com/strawberry-graphql/strawberry-graphql-django

Contributed by [Lauri Hintsala](https://github.com/la4de) [PR #949](https://github.com/strawberry-graphql/strawberry/pull/949/)


0.64.2 - 2021-05-26
-------------------

This release fixes that enum values yielded from async generators were not resolved
properly.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #969](https://github.com/strawberry-graphql/strawberry/pull/969/)


0.64.1 - 2021-05-23
-------------------

This release fixes a max recursion depth error in the AIOHTTP subscription
implementation.

Contributed by [Jonathan Ehwald](https://github.com/DoctorJohn) [PR #966](https://github.com/strawberry-graphql/strawberry/pull/966/)


0.64.0 - 2021-05-22
-------------------

This release adds an extensions field to the `GraphQLHTTPResponse` type and also exposes it in the view's response.

This field gets populated by Strawberry extensions: https://strawberry.rocks/docs/guides/extensions#get-results

Contributed by [lijok](https://github.com/lijok) [PR #903](https://github.com/strawberry-graphql/strawberry/pull/903/)


0.63.2 - 2021-05-22
-------------------

Add `root_value` to `ExecutionContext` type so that it can be accessed in
extensions.

Example:

```python
import strawberry
from strawberry.extensions import Extension


class MyExtension(Extension):
    def on_request_end(self):
        root_value = self.execution_context.root_value
        # do something with the root_value
```

Contributed by [Jonathan Kim](https://github.com/jkimbo) [PR #959](https://github.com/strawberry-graphql/strawberry/pull/959/)


0.63.1 - 2021-05-20
-------------------

New deployment process to release new Strawberry releases

[Marco Acierno](https://github.com/marcoacierno) [PR #957](https://github.com/strawberry-graphql/strawberry/pull/957/)


0.63.0 - 2021-05-19
-------------------

This release adds extra values to the ExecutionContext object so that it can be
used by extensions and the `Schema.process_errors` function.

The full ExecutionContext object now looks like this:

```python
from graphql import ExecutionResult as GraphQLExecutionResult
from graphql.error.graphql_error import GraphQLError
from graphql.language import DocumentNode as GraphQLDocumentNode


@dataclasses.dataclass
class ExecutionContext:
    query: str
    context: Any = None
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = None

    graphql_document: Optional[GraphQLDocumentNode] = None
    errors: Optional[List[GraphQLError]] = None
    result: Optional[GraphQLExecutionResult] = None
```

and can be accessed in any of the extension hooks:

```python
from strawberry.extensions import Extension


class MyExtension(Extension):
    def on_request_end(self):
        result = self.execution_context.result
        # Do something with the result


schema = strawberry.Schema(query=Query, extensions=[MyExtension])
```

---

Note: This release also removes the creation of an ExecutionContext object in the web
framework views. If you were relying on overriding the `get_execution_context`
function then you should change it to `get_request_data` and use the
`strawberry.http.parse_request_data` function to extract the pieces of data
needed from the incoming request.

0.62.1 - 2021-05-19
-------------------

This releases fixes an issue with the debug server that prevented the
usage of dataloaders, see: https://github.com/strawberry-graphql/strawberry/issues/940

0.62.0 - 2021-05-19
-------------------

This release adds support for GraphQL subscriptions to the AIOHTTP integration.
Subscription support works out of the box and does not require any additional
configuration.

Here is an example how to get started with subscriptions in general. Note that by
specification GraphQL schemas must always define a query, even if only subscriptions
are used.

```python
import asyncio
import typing
import strawberry


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> typing.AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)


@strawberry.type
class Query:
    @strawberry.field
    def _unused(self) -> str:
        return ""


schema = strawberry.Schema(subscription=Subscription, query=Query)
```

0.61.3 - 2021-05-13
-------------------

Fix `@requires(fields: ["email"])` and `@provides(fields: ["name"])` usage on a Federation field

You can use `@requires` to specify which fields you need to resolve a field

```python
import strawberry


@strawberry.federation.type(keys=["id"], extend=True)
class Product:
    id: strawberry.ID = strawberry.federation.field(external=True)
    code: str = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: strawberry.ID, code: str):
        return cls(id=id, code=code)

    @strawberry.federation.field(requires=["code"])
    def my_code(self) -> str:
        return self.code
```

`@provides` can be used to specify what fields are going to be resolved
by the service itself without having the Gateway to contact the external service
to resolve them.

0.61.2 - 2021-05-08
-------------------

This release adds support for the info param in resolve_reference:

```python
@strawberry.federation.type(keys=["upc"])
class Product:
    upc: str
    info: str

    @classmethod
    def resolve_reference(cls, info, upc):
        return Product(upc, info)
```

> Note: resolver reference is used when using Federation, similar to [Apollo server's __resolveReference](https://apollographql.com/docs/federation/api/apollo-federation/#__resolvereference)

0.61.1 - 2021-05-05
-------------------

This release extends the `strawberry server` command to allow the specification
of a schema symbol name within a module:

```sh
strawberry server mypackage.mymodule:myschema
```

The schema symbol name defaults to `schema` making this change backwards compatible.

0.61.0 - 2021-05-04
-------------------

This release adds file upload support to the [Sanic](https://sanicframework.org)
integration. No additional configuration is required to enable file upload support.

The following example shows how a file upload based mutation could look like:

```python
import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return text_file.read().decode()
```

0.60.0 - 2021-05-04
-------------------

This release adds an `export-schema` command to the Strawberry CLI.
Using the command you can print your schema definition to your console.
Pipes and redirection can be used to store the schema in a file.

Example usage:

```sh
strawberry export-schema mypackage.mymodule:myschema > schema.graphql
```

0.59.1 - 2021-05-04
-------------------

This release fixes an issue that prevented using `source` as name of an argument

0.59.0 - 2021-05-03
-------------------

This release adds an [aiohttp](https://github.com/aio-libs/aiohttp) integration for
Strawberry. The integration provides a `GraphQLView` class which can be used to
integrate Strawberry with aiohttp:

```python
import strawberry
from aiohttp import web
from strawberry.aiohttp.views import GraphQLView


@strawberry.type
class Query:
    pass


schema = strawberry.Schema(query=Query)

app = web.Application()

app.router.add_route("*", "/graphql", GraphQLView(schema=schema))
```

0.58.0 - 2021-05-03
-------------------

This release adds a function called `create_type` to create a Strawberry type from a list of fields.

```python
import strawberry
from strawberry.tools import create_type


@strawberry.field
def hello(info) -> str:
    return "World"


def get_name(info) -> str:
    return info.context.user.name


my_name = strawberry.field(name="myName", resolver=get_name)

Query = create_type("Query", [hello, my_name])

schema = strawberry.Schema(query=Query)
```

0.57.4 - 2021-04-28
-------------------

This release fixes an issue when using nested lists, this now works properly:

```python
def get_polygons() -> List[List[float]]:
    return [[2.0, 6.0]]


@strawberry.type
class Query:
    polygons: List[List[float]] = strawberry.field(resolver=get_polygons)


schema = strawberry.Schema(query=Query)

query = "{ polygons }"

result = schema.execute_sync(query, root_value=Query())
```

0.57.3 - 2021-04-27
-------------------

This release fixes support for generic types so that now we can also use generics for input types:

```python
T = typing.TypeVar("T")


@strawberry.input
class Input(typing.Generic[T]):
    field: T


@strawberry.type
class Query:
    @strawberry.field
    def field(self, input: Input[str]) -> str:
        return input.field
```

0.57.2 - 2021-04-19
-------------------

This release fixes a bug that prevented from extending a generic type when
passing a type, like here:

```python
T = typing.TypeVar("T")


@strawberry.interface
class Node(typing.Generic[T]):
    id: strawberry.ID

    def _resolve(self) -> typing.Optional[T]:
        return None


@strawberry.type
class Book(Node[str]):
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> typing.List[Book]:
        return list()
```

0.57.1 - 2021-04-17
-------------------

Fix converting pydantic objects to strawberry types using `from_pydantic` when having a falsy value like 0 or ''.

0.57.0 - 2021-04-14
-------------------

Add a `process_errors` method to `strawberry.Schema` which logs all exceptions during execution to a `strawberry.execution` logger.

0.56.3 - 2021-04-13
-------------------

This release fixes the return type value from info argument of resolver.

0.56.2 - 2021-04-07
-------------------

This release improves Pydantic support to support default values and factories.

0.56.1 - 2021-04-06
-------------------

This release fixes the pydantic integration where you couldn't
convert objects to pydantic instance when they didn't have a
default value.

0.56.0 - 2021-04-05
-------------------

Add --app-dir CLI option to specify where to find the schema module to load when using
the debug server.

For example if you have a _schema_ module in a _my_app_ package under ./src, then you
can run the debug server with it using:

```bash
strawberry server --app-dir src my_app.schema
```

0.55.0 - 2021-04-05
-------------------

Add support for `default` and `default_factory` arguments in `strawberry.field`

```python
@strawberry.type
class Droid:
    name: str = strawberry.field(default="R2D2")
    aka: List[str] = strawberry.field(default_factory=lambda: ["Artoo"])
```

0.54.0 - 2021-04-03
-------------------

Internal refactoring.

* Renamed `StrawberryArgument` to `StrawberryArgumentAnnotation`
* Renamed `ArgumentDefinition` to `StrawberryArgument`
    * Renamed `ArgumentDefinition(type: ...)` argument to
      `StrawberryArgument(type_: ...)`

0.53.4 - 2021-04-03
-------------------

Fixed issue with django multipart/form-data uploads

0.53.3 - 2021-04-02
-------------------

Fix issue where StrawberryField.graphql_name would always be camelCased

0.53.2 - 2021-04-01
-------------------

This release fixes an issue with the generated `__eq__` and `__repr__` methods when defining
fields with resolvers.

This now works properly:

```python
@strawberry.type
class Query:
    a: int

    @strawberry.field
    def name(self) -> str:
        return "A"


assert Query(1) == Query(1)
assert Query(1) != Query(2)
```

0.53.1 - 2021-03-31
-------------------

Gracefully handle user-induced subscription errors.

0.53.0 - 2021-03-30
-------------------

* `FieldDefinition` has been absorbed into `StrawberryField` and now no longer exists.

* `FieldDefinition.origin_name` and `FieldDefinition.name`  have been replaced with
  `StrawberryField.python_name` and `StrawberryField.graphql_name`. This should help
  alleviate some backend confusion about which should be used for certain situations.

* `strawberry.types.type_resolver.resolve_type` has been split into
  `resolve_type_argument` and `_resolve_type` (for arguments) until `StrawberryType` is
  implemented to combine them back together. This was done to reduce the scope of this
  PR and defer changing `ArgumentDefinition` (future `StrawberryArgument`) until a
  different PR.

> Note: The constructor signature for `StrawberryField` has `type_` as an argument
> instead of `type` as was the case for `FieldDefinition`. This is done to prevent
> shadowing of builtins.

> Note: `StrawberryField.name` still exists because of the way dataclass `Field`s
work, but is an alias for `StrawberryField.python_name`.

0.52.1 - 2021-03-28
-------------------

Include `field_nodes` in Strawberry info object.

0.52.0 - 2021-03-23
-------------------

Change `get_context` to be async for sanic integration

0.51.1 - 2021-03-22
-------------------

Configures GraphiQL to attach CSRF cookies as request headers sent to the GQL server.

0.51.0 - 2021-03-22
-------------------

Expose Strawberry Info object instead of GraphQLResolveInfo in resolvers

0.50.3 - 2021-03-22
-------------------

Django 3.2 support

0.50.2 - 2021-03-22
-------------------

Raise exception when un-serializable payload is provided to the Django view.

0.50.1 - 2021-03-18
-------------------

This release fixes a regression with the django sending the wrong content type.

0.50.0 - 2021-03-18
-------------------

This release updates get_context in the django integration to also receive a temporal response object that can be used to set headers, cookies and status code.


```
@strawberry.type
class Query:
    @strawberry.field
    def abc(self, info: strawberry.Info) -> str:
        info.context.response.status_code = 418

        return "ABC"
```

0.49.2 - 2021-03-18
-------------------

This releases changes how we define resolvers internally, now we have one single resolver for async and sync code.

0.49.1 - 2021-03-14
-------------------

Fix bug when using arguments inside a type that uses typing.Generics

0.49.0 - 2021-03-12
-------------------

This releases updates the ASGI class to make it easier to override `get_http_response`.

`get_http_response` has been now removed from strawberry.asgi.http and been moved to be
a method on the ASGI class.

A new `get_graphiql_response` method has been added to make it easier to provide a different GraphiQL interface.

0.48.3 - 2021-03-11
-------------------

This release updates `get_context` in the asgi integration to also
receive a temporal response object that can be used to set headers
and cookies.

0.48.2 - 2021-03-09
-------------------

This release fixes a bug when using the debug server and upload a file

0.48.1 - 2021-03-03
-------------------

Fix DataLoader docs typo.

0.48.0 - 2021-03-02
-------------------

# New Features
Added support for sanic webserver.

# Changelog
`ExecutionResult` was erroneously defined twice in the repository. The entry in `strawberry.schema.base` has been removed. If you were using it, switch to using
`strawberry.types.ExecutionResult` instead:

```python
from strawberry.types import ExecutionResult
```

0.47.1 - 2021-03-02
-------------------

Enable using .get for django context as well as for the square brackets notation.

0.47.0 - 2021-02-28
-------------------

Enable dot notation for django context request

0.46.0 - 2021-02-26
-------------------

Supporting multipart file uploads on Flask

0.45.4 - 2021-02-16
-------------------

Expose execution info under `strawberry.types.Info`

0.45.3 - 2021-02-08
-------------------

Fixes mypy failing when casting in enum decorator

0.45.2 - 2021-02-08
-------------------

Suggest installing the debug server on the getting started docs, so examples can work without import errors of uvicorn

0.45.1 - 2021-01-31
-------------------

Fix Generic name generation to use the custom name specified in Strawberry if available

```python
@strawberry.type(name="AnotherName")
class EdgeName:
    node: str


@strawberry.type
class Connection(Generic[T]):
    edge: T
```

will result in `AnotherNameConnection`, and not `EdgeNameConnection` as before.

0.45.0 - 2021-01-27
-------------------

This release add the ability to disable query validation by setting
`validate_queries` to `False`

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello"


schema = strawberry.Schema(Query, validate_queries=validate_queries)
```

0.44.12 - 2021-01-23
--------------------

This release adds support for MyPy==0.800

0.44.11 - 2021-01-22
--------------------

Fix for a duplicated input types error.

0.44.10 - 2021-01-22
--------------------

Internal codebase refactor. Clean up, consolidate, and standardize the conversion layer
between Strawberry types and GraphQL Core types; with room for further future
abstraction to support other GraphQL backends.

0.44.9 - 2021-01-22
-------------------

Improves typing when decorating an enum with kwargs like description and name. Adds more mypy tests.

0.44.8 - 2021-01-20
-------------------

This releases fixes a wrong dependency issue

0.44.7 - 2021-01-13
-------------------

Supporting multipart uploads as described here: https://github.com/jaydenseric/graphql-multipart-request-spec for ASGI.

0.44.6 - 2021-01-02
-------------------

Fix Strawberry to handle multiple subscriptions at the same time

0.44.5 - 2020-12-28
-------------------

Pass `execution_context_class` to Schema creation

0.44.4 - 2020-12-27
-------------------

Add support for converting more pydantic types

- pydantic.EmailStr
- pydantic.AnyUrl
- pydantic.AnyHttpUrl
- pydantic.HttpUrl
- pydantic.PostgresDsn
- pydantic.RedisDsn

0.44.3 - 2020-12-16
-------------------

This releases fixes an issue where methods marked as field were
removed from the class.

0.44.2 - 2020-11-22
-------------------

Validate the schema when it is created instead of at runtime.

0.44.1 - 2020-11-20
-------------------

This release adds support for strawberry.federation.field under mypy.

0.44.0 - 2020-11-19
-------------------

Creation of a `[debug-server]` extra, which is required to get going quickly with this project!

```
pip install strawberry-graphql
```

Will now install the primary portion of of the framework, allowing you to build your GraphQL
schema using the dataclasses pattern.

To get going quickly, you can install `[debug-server]` which brings along a server which allows
you to develop your API dynamically, assuming your schema is defined in the `app` module:

```
pip install 'strawberry-graphql[debug-server]'
strawberry server app
```

Typically, in a production environment, you'd want to bring your own server :)

0.43.2 - 2020-11-19
-------------------

This release fixes an issue when using unions inside generic types, this is now
supported:


```python
@strawberry.type
class Dog:
    name: str


@strawberry.type
class Cat:
    name: str


@strawberry.type
class Connection(Generic[T]):
    nodes: List[T]


@strawberry.type
class Query:
    connection: Connection[Union[Dog, Cat]]
```

0.43.1 - 2020-11-18
-------------------

This releases fixes an issue with Strawberry requiring Pydantic even when not used.

0.43.0 - 2020-11-18
-------------------

This release adds support for creating types from Pydantic models. Here's an
example:

```python
import strawberry

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class UserModel(BaseModel):
    id: int
    name = "John Doe"
    signup_ts: Optional[datetime] = None
    friends: List[int] = []


@strawberry.experimental.pydantic.type(
    model=UserModel, fields=["id", "name", "friends"]
)
class UserType:
    pass
```

0.42.7 - 2020-11-18
-------------------

Add some checks to make sure the types passed to `.union` are valid.

0.42.6 - 2020-11-18
-------------------

Fix issue preventing reusing the same resolver for multiple fields, like here:

```python
def get_name(self) -> str:
    return "Name"


@strawberry.type
class Query:
    name: str = strawberry.field(resolver=get_name)
    name_2: str = strawberry.field(resolver=get_name)
```

0.42.5 - 2020-11-18
-------------------

Another small improvement for mypy, this should prevent mypy from crashing when it can't find a type

0.42.4 - 2020-11-18
-------------------

This release fixes another issue with mypy where it wasn't able to identify strawberry fields.
It also now knows that fields with resolvers aren't put in the __init__ method of the class.

0.42.3 - 2020-11-17
-------------------

This release type improves support for strawberry.field in mypy,
now we don't get `Attributes without a default cannot follow attributes with one`
when using strawberry.field before a type without a default.

0.42.2 - 2020-11-17
-------------------

Bugfix to allow the use of `UNSET` as a default value for arguments.

```python
import strawberry
from strawberry.arguments import UNSET, is_unset


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: Optional[str] = UNSET) -> str:
        if is_unset(name):
            return "Hi there"
        return "Hi {name}"


schema = strawberry.Schema(query=Query)

result = schema.execute_async("{ hello }")
assert result.data == {"hello": "Hi there"}

result = schema.execute_async('{ hello(name: "Patrick" }')
assert result.data == {"hello": "Hi Patrick"}
```

SDL:

```graphql
type Query {
  hello(name: String): String!
}
```

0.42.1 - 2020-11-17
-------------------

This release improves mypy support for strawberry.field

0.42.0 - 2020-11-17
-------------------

* Completely revamped how resolvers are created, stored, and managed by
  StrawberryField. Now instead of monkeypatching a `FieldDefinition` object onto
  the resolver function itself, all resolvers are wrapped inside of a
  `StrawberryResolver` object with the useful properties.
* `arguments.get_arguments_from_resolver` is now the
  `StrawberryResolver.arguments` property
* Added a test to cover a situation where a field is added to a StrawberryType
  manually using `dataclasses.field` but not annotated. This was previously
  uncaught.

0.41.1 - 2020-11-14
-------------------

This release fixes an issue with forward types

0.41.0 - 2020-11-06
-------------------

This release adds a built-in dataloader. Example:

```python
async def app():
    async def idx(keys):
        return keys

    loader = DataLoader(load_fn=idx)

    [value_a, value_b, value_c] = await asyncio.gather(
        loader.load(1),
        loader.load(2),
        loader.load(3),
    )

    assert value_a == 1
    assert value_b == 2
    assert value_c == 3
```

0.40.2 - 2020-11-05
-------------------

Allow interfaces to implement other interfaces.
This may be useful if you are using the relay pattern
or if you want to model base interfaces that can be extended.

Example:
```python
import strawberry


@strawberry.interface
class Error:
    message: str


@strawberry.interface
class FieldError(Error):
    message: str
    field: str


@strawberry.type
class PasswordTooShort(FieldError):
    message: str
    field: str
    fix: str
```
Produces the following SDL:
```graphql
interface Error {
  message: String!
}

interface FieldError implements Error {
  message: String!
  field: String!
}

type PasswordTooShort implements FieldError & Error {
  message: String!
  field: String!
  fix: String!
}
```

0.40.1 - 2020-11-05
-------------------

Fix mypy plugin to handle bug where the `types` argument to `strawberry.union` is passed in as a keyword argument instead of a position one.

```python
MyUnion = strawberry.union(types=(TypeA, TypeB), name="MyUnion")
```

0.40.0 - 2020-11-03
-------------------

This release adds a new AsyncGraphQLView for django.

0.39.4 - 2020-11-02
-------------------

Improve typing for `field` and `StrawberryField`.

0.39.3 - 2020-10-30
-------------------

This release disable implicit re-export of modules. This fixes Strawberry for you if you were using `implicit_reexport = False` in your MyPy config.

0.39.2 - 2020-10-29
-------------------

This fixes the prettier pre-lint check.

0.39.1 - 2020-10-28
-------------------

Fix issue when using `strawberry.enum(module.EnumClass)` in mypy

0.39.0 - 2020-10-27
-------------------

This release adds support to mark a field as deprecated via `deprecation_reason`

0.38.1 - 2020-10-27
-------------------

Set default value to null in the schema when it's set to None

0.38.0 - 2020-10-27
-------------------

Register UUID's as a custom scalar type instead of the ID type.

⚠️ This is a potential breaking change because inputs of type UUID are now parsed as instances of uuid.UUID instead of strings as they were before.

0.37.7 - 2020-10-27
-------------------

This release fixes a bug when returning list in async resolvers

0.37.6 - 2020-10-23
-------------------

This release improves how we check for enums

0.37.5 - 2020-10-23
-------------------

This release improves how we handle enum values when returning lists of enums.

0.37.4 - 2020-10-22
-------------------

This releases adds a workaround to prevent mypy from crashing in specific occasions

0.37.3 - 2020-10-22
-------------------

This release fixes an issue preventing to return enums in lists

0.37.2 - 2020-10-21
-------------------

This release improves support for strawberry.enums when type checking with mypy.

0.37.1 - 2020-10-20
-------------------

Fix ASGI view to call `get_context` during a websocket request

0.37.0 - 2020-10-18
-------------------

Add support for adding a description to field arguments using the [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) type:

```python
from typing import Annotated


@strawberry.type
class Query:
    @strawberry.field
    def user_by_id(
        id: Annotated[str, strawberry.argument(description="The ID of the user")]
    ) -> User: ...
```

which results in the following schema:

```graphql
type Query {
  userById(
    """The ID of the user"""
    id: String
  ): User!
}
```

**Note:** if you are not using Python v3.9 or greater you will need to import `Annotated` from `typing_extensions`

0.36.4 - 2020-10-17
-------------------

This release adds support for using strawberry.enum as a function with MyPy,
this is now valid typed code:

```python
from enum import Enum

import strawberry


class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"


Flavour = strawberry.enum(IceCreamFlavour)
```

0.36.3 - 2020-10-16
-------------------

Add `__str__` to `Schema` to allow printing schema sdl with `str(schema)`

0.36.2 - 2020-10-12
-------------------

Extend support for parsing isoformat datetimes,
adding a dependency on the `dateutil` library.
For example: "2020-10-12T22:00:00.000Z"
can now be parsed as a datetime with a UTC timezone.

0.36.1 - 2020-10-11
-------------------

Add `schema.introspect()` method to return introspection result of the schema.
This might be useful for tools like `apollo codegen` or `graphql-voyager` which
expect a full json representation of the schema

0.36.0 - 2020-10-06
-------------------

This releases adds a new extension for OpenTelemetry.

```python
import asyncio

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
)

import strawberry
from strawberry.extensions.tracing import OpenTelemetryExtension


trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleExportSpanProcessor(ConsoleSpanExporter())
)


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    async def user(self, name: str) -> User:
        await asyncio.sleep(0.1)
        return User(name)


schema = strawberry.Schema(Query, extensions=[OpenTelemetryExtension])
```

0.35.5 - 2020-10-05
-------------------

This release disables tracing for default resolvers and introspection queries

0.35.4 - 2020-10-05
-------------------

This releases allows UNSET to be used anywhere and prevents mypy to report an error.

0.35.3 - 2020-10-05
-------------------

This releases adds support for strawberry.union inside mypy.

0.35.2 - 2020-10-04
-------------------

This release fixes an issue with the extension runner and async resolvers

0.35.1 - 2020-10-02
-------------------

Fixed bug where you couldn't use the same Union type multiple times in a schema.

0.35.0 - 2020-10-02
-------------------

Added `strawberry.Private` type to mark fields as "private" so they don't show up in the GraphQL schema.

Example:

```python
import strawberry


@strawberry.type
class User:
    age: strawberry.Private[int]

    @strawberry.field
    def age_in_months(self) -> int:
        return self.age * 12
```

0.34.2 - 2020-10-01
-------------------

Fix typo in type_resolver.py

0.34.1 - 2020-09-30
-------------------

This release fixes an issue with mypy when doing the following:

```python
import strawberry


@strawberry.type
class User:
    name: str = strawberry.field(description="Example")
```

0.34.0 - 2020-09-30
-------------------

This release adds support for Apollo Tracing and support for creating Strawberry
extensions, here's how you can enable Apollo tracing:

```python
from strawberry.extensions.tracing import ApolloTracingExtension

schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension])
```

And here's an example of custom extension:

```python
from strawberry.extensions import Extension


class MyExtension(Extension):
    def get_results(self):
        return {"example": "this is an example for an extension"}


schema = strawberry.Schema(query=Query, extensions=[MyExtension])
```

0.33.1 - 2020-09-25
-------------------

This release fixes an issue when trying to print a type
with a UNSET default value

0.33.0 - 2020-09-24
-------------------

* `UnionDefinition` has been renamed to `StrawberryUnion`
* `strawberry.union` now returns an instance of `StrawberryUnion` instead of a
dynamically generated class instance with a `_union_definition` attribute of
type `UnionDefinition`.

0.32.4 - 2020-09-22
-------------------

This release adds the `py.typed` file for better mypy support.

0.32.3 - 2020-09-07
-------------------

This release fixes another issue with extending types.

0.32.2 - 2020-09-07
-------------------

This releases fixes an issue when extending types, now
fields should work as they were working before even
when extending an existing type.

0.32.1 - 2020-09-06
-------------------

Improves tooling by adding `flake8-eradicate` to `flake8` `pre-commit` hook..

0.32.0 - 2020-09-06
-------------------

Previously, `strawberry.field` had redundant arguments for the resolver, one for
when `strawberry.field` was used as a decorator, and one for when it was used as
a function. These are now combined into a single argument.

The `f` argument of `strawberry.field` no longer exists. This is a
backwards-incompatible change, but should not affect many users. The `f`
argument was the first argument for `strawberry.field` and its use was only
documented without the keyword. The fix is very straight-forward: replace any
`f=` kwarg with `resolver=`.

```python
@strawberry.type
class Query:
    my_int: int = strawberry.field(f=lambda: 5)
    # becomes
    my_int: int = strawberry.field(resolver=lambda: 5)

    # no change
    @strawberry.field
    def my_float(self) -> float:
        return 5.5
```

Other (minor) breaking changes
* `MissingArgumentsAnnotationsError`'s message now uses the original Python
field name instead of the GraphQL field name. The error can only be thrown while
instantiating a strawberry.field, so the Python field name should be more
helpful.
* As a result, `strawberry.arguments.get_arguments_from_resolver()` now only
takes one field -- the `resolver` Callable.
* `MissingFieldAnnotationError` is now thrown when a strawberry.field is not
type-annotated but also has no resolver to determine its type

0.31.1 - 2020-08-26
-------------------

This release fixes the Flask view that was returning 400 when there were errors
in the GraphQL results. Now it always returns 200.

0.31.0 - 2020-08-26
-------------------

Add `process_result` to views for Django, Flask and ASGI. They can be overridden
to provide a custom response and also to process results and errors.

It also removes `request` from Flask view's `get_root_value` and `get_context`
since request in Flask is a global.

Django example:

```python
# views.py
from django.http import HttpRequest
from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult


class GraphQLView(BaseGraphQLView):
    def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return {"data": result.data, "errors": result.errors or []}
```

Flask example:

```python
# views.py
from strawberry.flask.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult


class GraphQLView(BaseGraphQLView):
    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return {"data": result.data, "errors": result.errors or []}
```

ASGI example:

```python
from strawberry.asgi import GraphQL as BaseGraphQL
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from starlette.requests import Request

from .schema import schema


class GraphQL(BaseGraphQLView):
    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return {"data": result.data, "errors": result.errors or []}
```

0.30.1 - 2020-08-17
-------------------

This releases fixes the check for unset values.

0.30.0 - 2020-08-16
-------------------

Add functions `get_root_value` and `get_context` to views for Django, Flask and
ASGI. They can be overridden to provide custom values per request.

Django example:

```python
# views.py
from strawberry.django.views import GraphQLView as BaseGraphQLView


class GraphQLView(BaseGraphQLView):
    def get_context(self, request):
        return {
            "request": request,
            "custom_context_value": "Hi!",
        }

    def get_root_value(self, request):
        return {
            "custom_root_value": "🍓",
        }


# urls.py
from django.urls import path

from .views import GraphQLView
from .schema import schema

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema)),
]
```

Flask example:

```python
# views.py
from strawberry.flask.views import GraphQLView as BaseGraphQLView


class GraphQLView(BaseGraphQLView):
    def get_context(self, request):
        return {
            "request": request,
            "custom_context_value": "Hi!",
        }

    def get_root_value(self, request):
        return {
            "custom_root_value": "🍓",
        }


# app.py
from flask import Flask

from .views import GraphQLView
from .schema import schema

app = Flask(__name__)

app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view("graphql_view", schema=schema),
)
```


ASGI example:

```python
# app.py
from strawberry.asgi import GraphQL as BaseGraphQL

from .schema import schema


class GraphQL(BaseGraphQLView):
    async def get_context(self, request):
        return {
            "request": request,
            "custom_context_value": "Hi!",
        }

    async def get_root_value(self, request):
        return {
            "custom_root_value": "🍓",
        }


app = GraphQL(schema)
```

0.29.1 - 2020-08-07
-------------------

Support for `default_value` on inputs.

Usage:
```python
class MyInput:
    s: Optional[str] = None
    i: int = 0
```
```graphql
input MyInput {
  s: String = null
  i: Int! = 0
}
```

0.29.0 - 2020-08-03
-------------------

This release adds support for file uploads within Django.

We follow the following spec: https://github.com/jaydenseric/graphql-multipart-request-spec


Example:

```python
import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return text_file.read().decode()
```

0.28.5 - 2020-08-01
-------------------

Fix issue when reusing an interface

0.28.4 - 2020-07-28
-------------------

Fix issue when using generic types with federation

0.28.3 - 2020-07-27
-------------------

Add support for using lazy types inside generics.

0.28.2 - 2020-07-26
-------------------

This releae add support for UUID as field types. They will be
represented as GraphQL ID in the GraphQL schema.

0.28.1 - 2020-07-25
-------------------

This release fixes support for PEP-563, now you can safely use `from __future__ import annotations`,
like the following example:


```python
from __future__ import annotations


@strawberry.type
class Query:
    me: MyType = strawberry.field(name="myself")


@strawberry.type
class MyType:
    id: strawberry.ID
```

0.28.0 - 2020-07-24
-------------------

This releases brings a much needed internal refactor of how we generate
GraphQL types from class definitions. Hopefully this will make easier to
extend Strawberry in future.

There are some internal breaking changes, so if you encounter any issue
let us know and well try to help with the migration.

In addition to the internal refactor we also fixed some bugs and improved
the public api for the schema class. Now you can run queries directly
on the schema by running `schema.execute`, `schema.execute_sync` and
`schema.subscribe` on your schema.

0.27.5 - 2020-07-22
-------------------

Add websocket object to the subscription context.

0.27.4 - 2020-07-14
-------------------

This PR fixes a bug when declaring multiple non-named union types

0.27.3 - 2020-07-10
-------------------

Optimized signature reflection and added benchmarks.

0.27.2 - 2020-06-11
-------------------

This release fixes an issue when using named union types in generic types,
for example using an optional union. This is now properly supported:


```python
@strawberry.type
class A:
    a: int


@strawberry.type
class B:
    b: int


Result = strawberry.union("Result", (A, B))


@strawberry.type
class Query:
    ab: Optional[Result] = None
```

0.27.1 - 2020-06-11
-------------------

Fix typo in Decimal description

0.27.0 - 2020-06-10
-------------------

This release adds support for decimal type, example:


```python
@strawberry.type
class Query:
    @strawberry.field
    def example_decimal(self) -> Decimal:
        return Decimal("3.14159")
```

0.26.3 - 2020-06-10
-------------------

This release disables subscription in GraphiQL where it
is not supported.

0.26.2 - 2020-06-03
-------------------

Fixes a bug when using unions and lists together

0.26.1 - 2020-05-22
-------------------

Argument conversion doesn't populate missing args with defaults.
```python
@strawberry.field
def hello(self, null_or_unset: Optional[str] = UNSET, nullable: str = None) -> None:
    pass
```

0.26.0 - 2020-05-21
-------------------

This releases adds experimental support for apollo federation.

Here's an example:

```python
import strawberry


@strawberry.federation.type(extend=True, keys=["id"])
class Campaign:
    id: strawberry.ID = strawberry.federation.field(external=True)

    @strawberry.field
    def title(self) -> str:
        return f"Title for {self.id}"

    @classmethod
    def resolve_reference(cls, id):
        return Campaign(id)


@strawberry.federation.type(extend=True)
class Query:
    @strawberry.field
    def strawberry(self) -> str:
        return "🍓"


schema = strawberry.federation.Schema(query=Query, types=[Campaign])
```

0.25.6 - 2020-05-19
-------------------

Default values make input arguments nullable when the default is None.
```python
class Query:
    @strawberry.field
    def hello(self, i: int = 0, s: str = None) -> str:
        return s
```
```graphql
type Query {
  hello(i: Int! = 0, s: String): String!
}
```

0.25.5 - 2020-05-18
-------------------

Added sentinel value for input parameters that aren't sent by the clients.
It checks for when a field is unset.

0.25.4 - 2020-05-18
-------------------

Support for `default_value` on inputs and arguments.

Usage:
```python
class MyInput:
    s: Optional[str]
    i: int = 0
```
```graphql
input MyInput {
  s: String
  i: Int! = 0
}
```

0.25.3 - 2020-05-17
-------------------

Improves tooling by updating `pre-commit` hooks and adding `pre-commit` to
`pyproject.toml`.

0.25.2 - 2020-05-11
-------------------

Add support for setting `root_value` in asgi.

Usage:
```python
schema = strawberry.Schema(query=Query)
app = strawberry.asgi.GraphQL(schema, root_value=Query())
```

0.25.1 - 2020-05-08
-------------------

Fix error when a subscription accepted input arguments

0.25.0 - 2020-05-05
-------------------

This release add supports for named unions, now you can create
a new union type by writing:

```python
Result = strawberry.union("Result", (A, B), description="Example Result")
```

This also improves the support for Union and Generic types, as it
was broken before.

0.24.1 - 2020-04-29
-------------------

This release fixes a bug introduced by 0.24.0

0.24.0 - 2020-04-29
-------------------

This releases allows to use resolver without having
to specify root and info arguments:

```python
def function_resolver() -> str:
    return "I'm a function resolver"


def function_resolver_with_params(x: str) -> str:
    return f"I'm {x}"


@strawberry.type
class Query:
    hello: str = strawberry.field(resolver=function_resolver)
    hello_with_params: str = strawberry.field(resolver=function_resolver_with_params)


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "I'm a function resolver"

    @strawberry.field
    def hello_with_params(self, x: str) -> str:
        return f"I'm {x}"
```

This makes it easier to reuse existing functions and makes code
cleaner when not using info or root.

0.23.3 - 2020-04-29
-------------------

This release fixes the dependency of GraphQL-core

0.23.2 - 2020-04-25
-------------------

This releases updates the _debug server_ to serve the API on '/' as well as '/graphql'.

0.23.1 - 2020-04-20
-------------------

Removes the need for duplicate graphiql template file.

0.23.0 - 2020-04-19
-------------------

This releases replaces the playground with GraphiQL including the GraphiQL explorer plugin.

0.22.0 - 2020-04-19
-------------------

This release adds support for generic types, allowing
to reuse types, here's an example:

```python
T = typing.TypeVar("T")


@strawberry.type
class Edge(typing.Generic[T]):
    cursor: strawberry.ID
    node: T


@strawberry.type
class Query:
    @strawberry.field
    def int_edge(self, info, **kwargs) -> Edge[int]:
        return Edge(cursor=strawberry.ID("1"), node=1)
```

0.21.1 - 2020-03-25
-------------------

Update version of graphql-core to 3.1.0b2

0.21.0 - 2020-02-13
-------------------

Added a Flask view that allows you to query the schema and interact with it via GraphiQL.

Usage:

```python
# app.py
from strawberry.flask.views import GraphQLView
from your_project.schema import schema

app = Flask(__name__)

app.add_url_rule(
    "/graphql", view_func=GraphQLView.as_view("graphql_view", schema=schema)
)

if __name__ == "__main__":
    app.run(debug=True)
```

0.20.3 - 2020-02-11
-------------------

Improve datetime, date and time types conversion. Removes aniso dependency
and also adds support for python types, so now we can do use python datetime's types
instead of our custom scalar types.

0.20.2 - 2020-01-22
-------------------

This version adds support for Django 3.0

0.20.1 - 2020-01-15
-------------------

Fix directives bugs:

- Fix autogenerated `return` argument bug

- Fix include and skip failure bug

0.20.0 - 2020-01-02
-------------------

This release improves support for permissions (it is a breaking change).
Now you will receive the source and the arguments in the `has_permission` method,
so you can run more complex permission checks. It also allows to use permissions
on fields, here's an example:


```python
import strawberry

from strawberry.permission import BasePermission


class IsAdmin(BasePermission):
    message = "You are not authorized"

    def has_permission(self, source, info):
        return source.name.lower() == "Patrick" or _is_admin(info)


@strawberry.type
class User:
    name: str
    email: str = strawberry.field(permission_classes=[IsAdmin])


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAdmin])
    def user(self, info) -> str:
        return User(name="Patrick", email="example@email.com")
```

0.19.1 - 2019-12-20
-------------------

This releases removes support for async resolver in django
as they causes issues when accessing the databases.

0.19.0 - 2019-12-19
-------------------

This release improves support for django and asgi integration.

It allows to use async resolvers when using django. It also changes the status
code from 400 to 200 even if there are errors this makes it possible to still
use other fields even if one raised an error.

We also moved strawberry.contrib.django to strawberry.django, so if you're using
the django view make sure you update the paths.

0.18.3 - 2019-12-09
-------------------

Fix missing support for booleans when converting arguments

0.18.2 - 2019-12-09
-------------------

This releases fixes an issue when converting complex input types,
now it should support lists of complex types properly.

0.18.1 - 2019-11-03
-------------------

Set `is_type_of` only when the type implements an interface,
this allows to return different (but compatible) types in basic cases.

0.18.0 - 2019-10-31
-------------------

Refactored CLI folder structure, importing click commands from a subfolder. Follows click's complex example.

0.17.0 - 2019-10-30
-------------------

Add support for custom GraphQL scalars.

0.16.10 - 2019-10-30
--------------------

Tests are now run on GitHub actions on both python 3.7 and python3.8 🐍

0.16.9 - 2019-10-30
-------------------

Fixed some typos in contributing.md .

0.16.8 - 2019-10-29
-------------------

Fixed some typos in readme.md and contributing.md.

0.16.7 - 2019-10-28
-------------------

Minimal support for registering types without fields and abstract interface querying.

0.16.6 - 2019-10-27
-------------------

Grammar fixes - changed 'corresponding tests, if tests' to 'corresponding tests. If tests' and removed extraneous period from 'Provide specific examples to demonstrate the steps..'. Also made 'Enhancement' lowercase to stay consistent with its usage in documentation and changed 'on the Strawberry' to 'to Strawberry'.

0.16.5 - 2019-10-16
-------------------

Added issue template files (bug_report.md, feature_request.md, other_issues.md) and a pull request template file.

0.16.4 - 2019-10-14
-------------------

Fix execution of async resolvers.

0.16.3 - 2019-10-14
-------------------

Typo fix - changed the spelling from 'follwing' to 'following'.

0.16.2 - 2019-10-03
-------------------

Updated docs to provide reference on how to use Django view.

0.16.1 - 2019-09-29
-------------------

Removed custom representation for Strawberry types,
this should make using types much nicer.

0.16.0 - 2019-09-13
-------------------

Switched from `graphql-core-next` dependency to `graphql-core@^3.0.0a0`.

0.15.6 - 2019-09-11
-------------------

Fixes MYPY plugin

0.15.5 - 2019-09-10
-------------------

Add the flake8-bugbear linting plugin to catch likely bugs

0.15.4 - 2019-09-06
-------------------

Fixed conversion of enum when value was falsy.

0.15.3 - 2019-09-06
-------------------

Fixed issue when trying to convert optional arguments to a type

0.15.2 - 2019-09-06
-------------------

Fix issue with converting arguments with optional fields.

Thanks to [@sciyoshi](https://github.com/sciyoshi) for the fix!

0.15.1 - 2019-09-05
-------------------

Added a Django view that allows you to query the schema and interact with it via GraphiQL

Usage:

```python
# Install
# pip install "strawberry-graphql[django]"

# settings.py
INSTALLED_APPS = [
    ...,
    "strawberry.django",
]

# urls.py
from strawberry.django.views import GraphQLView
from your_project.schema import schema

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema)),
]
```

0.15.0 - 2019-09-04
-------------------

This release doesn't add any feature or fixes, but it fixes an issue with
checking for release files when submitting PRs ✨.

0.14.4 - 2019-09-01
-------------------

Fixes the conversion of Enums in resolvers, arguments and input types.

0.14.3 - 2019-09-01
-------------------

Add a mypy plugin that enables typechecking Strawberry types

0.14.2 - 2019-08-31
-------------------

Fix List types being converted to Optional GraphQL lists.

0.14.1 - 2019-08-25
-------------------

This release doesn't add any feature or fixes, it only introduces a GitHub
Action to let people know how to add a RELEASE.md file when submitting a PR.

0.14.0 - 2019-08-14
-------------------

Added support for defining query directives, example:

```python
import strawberry
from strawberry.directive import DirectiveLocation


@strawberry.type
class Query:
    cake: str = "made_in_switzerland"


@strawberry.directive(
    locations=[DirectiveLocation.FIELD], description="Make string uppercase"
)
def uppercase(value: str, example: str):
    return value.upper()


schema = strawberry.Schema(query=Query, directives=[uppercase])
```

0.13.4 - 2019-08-01
-------------------

Improve dict_to_type conversion by checking if the field has a different name or case

0.13.3 - 2019-07-23
-------------------

Fix field initialization not allowed when using `strawberry.field` in an `input` type

```python
@strawberry.input
class Say:
    what = strawberry.field(is_input=True)
```

0.13.2 - 2019-07-18
-------------------

Allow the usage of Union types in the mutations

```python
@strawberry.type
class A:
    x: int


@strawberry.type
class B:
    y: int


@strawberry.type
class Mutation:
    @strawberry.mutation
    def hello(self, info) -> Union[A, B]:
        return B(y=5)


schema = strawberry.Schema(query=A, mutation=Mutation)

query = """
mutation {
    hello {
        __typename

        ... on A {
            x
        }

        ... on B {
            y
        }
    }
}
"""
```

0.13.1 - 2019-07-17
-------------------

Fix missing fields when extending a class, now we can do this:


```python
@strawberry.type
class Parent:
    cheese: str = "swiss"

    @strawberry.field
    def friend(self, info) -> str:
        return "food"


@strawberry.type
class Schema(Parent):
    cake: str = "made_in_swiss"
```

0.13.0 - 2019-07-16
-------------------

This release adds field support for permissions

```python
import strawberry

from strawberry.permission import BasePermission


class IsAdmin(BasePermission):
    message = "You are not authorized"

    def has_permission(self, info):
        return False


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAdmin])
    def hello(self, info) -> str:
        return "Hello"
```

0.12.0 - 2019-06-25
-------------------

This releases adds support for ASGI 3.0

```python
from strawberry.asgi import GraphQL
from starlette.applications import Starlette

graphql_app = GraphQL(schema_module.schema, debug=True)

app = Starlette(debug=True)
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)
```

0.11.0 - 2019-06-07
-------------------

Added support for optional fields with default arguments in the GraphQL schema when default arguments are passed to the resolver.

Example:
 ```python
@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info, name: str = "world") -> str:
        return name
```

```graphql
type Query {
    hello(name: String = "world"): String
}
```

0.10.0 - 2019-05-28
-------------------

Fixed issue that was prevent usage of InitVars.
Now you can safely use InitVar to prevent fields from showing up in the schema:


```python
@strawberry.type
class Category:
    name: str
    id: InitVar[str]


@strawberry.type
class Query:
    @strawberry.field
    def category(self, info) -> Category:
        return Category(name="example", id="123")
```

0.9.1 - 2019-05-25
------------------

Fixed logo on PyPI

0.9.0 - 2019-05-24
------------------

Added support for passing resolver functions

```python
def resolver(root, info, par: str) -> str:
    return f"hello {par}"


@strawberry.type
class Query:
    example: str = strawberry.field(resolver=resolver)
```

Also we updated some of the dependencies of the project

0.8.0 - 2019-05-09
------------------

Added support for renaming fields. Example usage:
```python
@strawberry.type
class Query:
    example: str = strawberry.field(name="test")
```

0.7.0 - 2019-05-09
------------------

Added support for declaring interface by using `@strawberry.interface`
Example:
```python
@strawberry.interface
class Node:
    id: strawberry.ID
```

0.6.0 - 2019-05-02
------------------

This changes field to be lazy by default, allowing to use circular dependencies
when declaring types.

0.5.6 - 2019-04-30
------------------

Improve listing on pypi.org

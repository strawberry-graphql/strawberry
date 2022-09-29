CHANGELOG
=========

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
class MyModelStrawberry:
    ...

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
class MyInfo(Info)
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
The `JSON` scalar type represents JSON values as specified by [ECMA-404](http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf).
"""
scalar JSON
  @specifiedBy(
    url: "http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf"
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
        "strawberry", description="Our favourite",
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
    first_name: str = strawberry.field(
        directives=[Sensitive(reason=Reason.EXAMPLE)]
    )
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
    ]
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
    def field(
        self, x: List[str] = ["foo"], y: JSON = {"foo": 42}  # noqa: B006
    ) -> str:
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
strawberry_type: TypeDefinition = graphql_core_type.extensions[GraphQLCoreConverter.DEFINITION_BACKREF]
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

def some_resolver(info: Info) -> str:
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
def add_frosting(value: str, v: DirectiveValue[Cake], my_info: Info):
    # Arbitrary argument name when using `DirectiveValue` is supported!
    assert isinstance(v, Cake)
    if value in my_info.context["allergies"]:  # Info can now be accessed from directives!
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

schema = strawberry.Schema(
    query=Query, config=StrawberryConfig(auto_camel_case=False)
)
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

app.add_url_rule("/graphql", view_func=AsyncGraphQLView.as_view("graphql_view", schema=schema, **kwargs))
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
    STRAWBERRY = strawberry.enum_value(
        "strawberry", deprecation_reason="We ran out"
    )
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
    not_visible int
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
def response_check(self, info: Info) -> bool:
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
class ExampleGQL:
    ...

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
```grapqhl
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

@strawberry.experimental.pydantic.type(
    UserModel, use_pydantic_alias=False
)
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
    animal: Animal | None # This line no longer triggers a TypeError
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


@pytest.fixture()
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
class QueryA:
    ...


@strawberry.type
class QueryB:
    ...


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
  ]
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
    FORD = 'ford'
    TOYOTA = 'toyota'
    HONDA = 'honda'

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
def add_word(word: Word) -> bool:
	...
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

urlpatterns = [path("graphql", AsyncGraphQLView.as_view(schema=schema, graphiql=True, subscriptions_enabled=True))]
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
  }
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

class Query(MyType):
    ...
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
def create_flavour(self, info: Info) -> str:
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
validation_rules = (
  default_validation_rules + [depth_limit_validator(3)]
)

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

schema = strawberry.Schema(
    query=Query, config=StrawberryConfig(auto_camel_case=False)
)
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
        self,
        input_: Annotated[HelloInput, strawberry.argument(name="input")]
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
def create_flavour(
    self, flavour: IceCreamFlavour = IceCreamFlavour.STRAWBERRY
) -> str:
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
    def abc(self, info: Info) -> str:
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
    name = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: List[int] = []

@strawberry.experimental.pydantic.type(model=UserModel, fields=[
    'id',
    'name',
    'friends'
])
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
    def user_by_id(id: Annotated[str, strawberry.argument(description="The ID of the user")]) -> User:
        ...
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
    name: str = strawberry.field(description='Example')
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
        return {
            "example": "this is an example for an extension"
        }

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
    def process_result(self, request: HttpRequest, result: ExecutionResult) -> GraphQLHTTPResponse:
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
    async def process_result(self, request: Request, result: ExecutionResult) -> GraphQLHTTPResponse:
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
    hello_with_params: str = strawberry.field(
        resolver=function_resolver_with_params
    )


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
$ pip install 'strawberry-graphql[django]'

# settings.py
INSTALLED_APPS = [
    ...
    'strawberry.django',
]

# urls.py
from strawberry.django.views import GraphQLView
from your_project.schema import schema

urlpatterns = [
    path('graphql/', GraphQLView.as_view(schema=schema)),
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
        return 'food'

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
example: str = strawberry.field(name='test')
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

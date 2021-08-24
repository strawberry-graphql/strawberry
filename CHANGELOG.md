CHANGELOG
=========

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
pip install strawberry[asgi]
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

This relases fixes an issue with the generated `__eq__` and `__repr__` methods when defining
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
pip install strawberry-graphql[debug-server]
strawberry server app
```

Typically, in a production environment, you'd want to bring your own server :)

0.43.2 - 2020-11-19
-------------------

This release fixes an issue when usign unions inside generic types, this is now
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

This release improves how we handle enum values when returing lists of enums.

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
when extending an exising type.

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
ASGI. They can be overriden to provide custom values per request.

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

This release fixes the dependecy of GraphQL-core

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
this allows to return different (but compatibile) types in basic cases.

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
$ pip install strawberry-graphql[django]

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

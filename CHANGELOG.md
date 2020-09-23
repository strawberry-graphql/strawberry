CHANGELOG
=========

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

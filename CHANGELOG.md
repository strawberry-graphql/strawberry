CHANGELOG
=========

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

Added a Django view that allows you to query the schema and interact with it via GraphQL playground.

Usage:

```python

# Install
$ pip install strawberry-graphql[django]

# settings.py
INSTALLED_APPS = [
    ...
    'strawberry.contrib.django',
]

# urls.py
from strawberry.contrib.django.views import GraphQLView
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
from strawberry.directives import DirectiveLocation

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

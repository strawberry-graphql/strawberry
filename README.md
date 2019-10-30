<img src="https://github.com/strawberry-graphql/strawberry/raw/master/.github/logo.png" width="124" height="150">

# Strawberry GraphQL

> Python GraphQL library based on dataclasses

[![CircleCI](https://img.shields.io/circleci/token/307b40d5e152e074d34f84d30d226376a15667d5/project/github/strawberry-graphql/strawberry/master.svg?style=for-the-badge)](https://circleci.com/gh/strawberry-graphql/strawberry/tree/master)

## Installation

Install with:

```shell
pip install strawberry-graphql
```

## Getting Started

Create a file called `app.py` with the following code:

```python
import strawberry


@strawberry.type
class User:
    name: str
    age: int


@strawberry.type
class Query:
    @strawberry.field
    def user(self, info) -> User:
        return User(name="Patrick", age=100)


schema = strawberry.Schema(query=Query)
```

This will create a GraphQL schema defining a `User` type and a single query
field `user` that will return a hardcoded user.

To run the debug server run the following command:

```shell
strawberry server app
```

Open the debug server by clicking on the following link:
[http://0.0.0.0:8000/graphql](http://0.0.0.0:8000/graphql)

This will open a GraphQL playground where you can test the API.

### Type-checking

Strawberry comes with a [mypy] plugin that enables statically type-checking your GraphQL schema. To enable it, add the following lines to your `mypy.ini` configuration:

```ini
[mypy]
plugins = strawberry.ext.mypy_plugin
```

[mypy]: http://www.mypy-lang.org/

### Django Integration

A Django view is provided for adding a GraphQL endpoint to your application.

1. Add the app to your `INSTALLED_APPS`.
```python
INSTALLED_APPS = [
    ...
    'strawberry.contrib.django',
]
```

2. Add the view to your `urls.py` file.
```python
from strawberry.contrib.django.views import GraphQLView
from .schema import schema

urlpatterns = [
    ...,
    path('graphql', GraphQLView.as_view(schema=schema)),
]
```

## Contributing

We use [poetry](https://github.com/sdispater/poetry) to manage dependencies, to
get started follow these steps:

```shell
git clone https://github.com/strawberry-graphql/strawberry
cd strawberry
poetry install
poetry run pytest
```

This will install all the dependencies (including dev ones) and run the tests.

### Pre commit

We have a configuration for
[pre-commit](https://github.com/pre-commit/pre-commit), to add the hook run the
following command:

```shell
pre-commit install
```

## Links

- Project homepage: https://strawberry.rocks
- Repository: https://github.com/strawberry-graphql/strawberry
- Issue tracker: https://github.com/strawberry-graphql/strawberry/issues
  - In case of sensitive bugs like security vulnerabilities, please contact
    patrick.arminio@gmail.com directly instead of using the issue tracker. We value
    your effort to improve the security and privacy of this project!

## Licensing

The code in this project is licensed under MIT license. See [LICENSE](./LICENSE)
for more information.

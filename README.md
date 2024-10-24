<img src="https://github.com/strawberry-graphql/strawberry/raw/main/.github/logo.png" width="124" height="150">

# Strawberry GraphQL

> Python GraphQL library leveraging modern Python features like dataclasses and type hints to create GraphQL APIs.

[![CircleCI](https://img.shields.io/circleci/token/307b40d5e152e074d34f84d30d226376a15667d5/project/github/strawberry-graphql/strawberry/main.svg?style=for-the-badge)](https://circleci.com/gh/strawberry-graphql/strawberry/tree/main)
[![Discord](https://img.shields.io/discord/689806334337482765?label=discord&logo=discord&logoColor=white&style=for-the-badge&color=blue)](https://discord.gg/ZkRTEJQ)
[![PyPI](https://img.shields.io/pypi/v/strawberry-graphql?logo=pypi&logoColor=white&style=for-the-badge)](https://pypi.org/project/strawberry-graphql/)

## Quick Start

### Installation

```shell
pip install "strawberry-graphql[debug-server]"
```

### Basic Example

Create a new file `app.py`:

```python
import strawberry


@strawberry.type
class User:
    name: str
    age: int


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100)


schema = strawberry.Schema(query=Query)
```

Run the debug server:

```shell
strawberry server app
```

Visit [http://0.0.0.0:8000/graphql](http://0.0.0.0:8000/graphql) to access GraphiQL and explore your API.

## Features

### Type Checking with MyPy

Enable static type checking by adding to your `mypy.ini`:

```ini
[mypy]
plugins = strawberry.ext.mypy_plugin
```

### Django Integration

1. Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    "strawberry.django",  # Add this line
    # ... your other apps
]
```

2. Configure URL routing in `urls.py`:

```python
from strawberry.django.views import GraphQLView
from .schema import schema

urlpatterns = [
    path("graphql", GraphQLView.as_view(schema=schema)),
    # ... your other urls
]
```

### WebSocket Support

For GraphQL subscriptions over WebSockets:

```shell
pip install 'strawberry-graphql[debug-server]'
pip install 'uvicorn[standard]'
```

## Testing

Strawberry provides built-in testing utilities through `BaseGraphQLTestClient`:

```python
from strawberry.test import BaseGraphQLTestClient


class MyTestClient(BaseGraphQLTestClient):
    def request(self, body, headers=None, files=None):
        # Implement request logic
        pass


def test_query():
    client = MyTestClient(http_client)
    response = client.query(
        """
        {
            user {
                name
                age
            }
        }
    """
    )

    assert response.data["user"]["name"] == "Patrick"
    assert not response.errors
```

## Examples & Resources

- [Official Examples Repository](https://github.com/strawberry-graphql/examples)
- [Full-stack Demo (Starlette + SQLAlchemy + TypeScript + Next.js)](https://github.com/jokull/python-ts-graphql-demo)
- [Quart Integration Tutorial](https://github.com/rockyburt/Ketchup)

## Development

### Setting Up Development Environment

```shell
git clone https://github.com/strawberry-graphql/strawberry
cd strawberry
poetry install --with integrations
poetry run pytest
```

### Pre-commit Hooks

```shell
pre-commit install
```

## Community & Support

- Documentation: [https://strawberry.rocks](https://strawberry.rocks)
- GitHub Repository: [https://github.com/strawberry-graphql/strawberry](https://github.com/strawberry-graphql/strawberry)
- Issue Tracker: [https://github.com/strawberry-graphql/strawberry/issues](https://github.com/strawberry-graphql/strawberry/issues)
- Security Issues: Contact patrick.arminio@gmail.com directly

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

![Recent Activity](https://images.repography.com/0/strawberry-graphql/strawberry/recent-activity/d751713988987e9331980363e24189ce.svg)

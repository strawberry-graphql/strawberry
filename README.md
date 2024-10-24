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

Strawberry provides built-in testing utilities through `BaseGraphQLTestClient`. Here are three different implementations using popular HTTP clients:

### 1. Testing with httpx

```python
from strawberry.test import BaseGraphQLTestClient
import httpx

class HttpxTestClient(BaseGraphQLTestClient):
    def __init__(self):
        self.client = httpx.Client(base_url="http://localhost:8000")
    
    def request(self, body: str, headers=None, files=None):
        headers = headers or {}
        response = self.client.post(
            "/graphql",
            json=body,
            headers=headers,
            files=files
        )
        return response.json()

def test_query():
    client = HttpxTestClient()
    
    response = client.query("""
        { 
            user { 
                name 
                age 
            } 
        }
    """)
    
    assert response.data["user"]["name"] == "Patrick"
    assert not response.errors
```

### 2. Testing with requests

```python
from strawberry.test import BaseGraphQLTestClient
from requests import Session

class RequestsTestClient(BaseGraphQLTestClient):
    def __init__(self):
        self.client = Session()
        self.client.base_url = "http://localhost:8000"
    
    def request(self, body: str, headers=None, files=None):
        headers = headers or {}
        response = self.client.post(
            f"{self.client.base_url}/graphql",
            json=body,
            headers=headers,
            files=files
        )
        return response.json()

def test_query_with_variables():
    client = RequestsTestClient()
    
    response = client.query(
        """
        query GetUser($id: ID!) { 
            user(id: $id) { 
                name 
                age 
            } 
        }
        """,
        variables={"id": "123"}
    )
    
    assert response.data["user"]["name"] == "Patrick"
    assert not response.errors
```

### 3. Testing with aiohttp (async)

```python
from strawberry.test import BaseGraphQLTestClient
import aiohttp
import asyncio

class AiohttpTestClient(BaseGraphQLTestClient):
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def async_request(self, body: str, headers=None, files=None):
        headers = headers or {}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/graphql",
                json=body,
                headers=headers
            ) as response:
                return await response.json()
    
    def request(self, body: str, headers=None, files=None):
        return asyncio.run(self.async_request(body, headers, files))

def test_async_query():
    client = AiohttpTestClient()
    
    response = client.query("""
        { 
            user { 
                name 
                age 
            } 
        }
    """)
    
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

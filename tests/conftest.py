import pytest

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


@pytest.fixture
def schema():
    return strawberry.Schema(query=Query)


def pytest_emoji_xfailed(config):
    return "🤷‍♂️ ", "XFAIL 🤷‍♂️ "

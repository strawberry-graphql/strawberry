from typing import Any

import pytest
from pytest_codspeed import BenchmarkFixture

import strawberry
from strawberry.permission import BasePermission


class Allowed(BasePermission):
    def has_permission(self, source, info, **kwargs: Any) -> bool:
        return info.context["allowed"]


class InvalidValue(Exception):
    pass


@strawberry.type
class Failure:
    message: str


@strawberry.type
class Success:
    value: int


class Handler(strawberry.ExceptionHandler[InvalidValue, Failure]):
    def handle(self, exception: InvalidValue, *, field, info) -> Failure:
        return Failure(message=str(exception))


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[Allowed])
    def protected(self) -> int:
        return 42

    @strawberry.field
    def checked(self) -> Success | Failure:
        raise InvalidValue("invalid")


@pytest.mark.parametrize("operation", ["permission", "handled_error"])
def test_permission_and_error(benchmark: BenchmarkFixture, operation: str):
    schema = strawberry.Schema(query=Query, exception_handlers=[Handler()])
    query = (
        "{ protected }"
        if operation == "permission"
        else "{ checked { ... on Failure { message } } }"
    )
    result = benchmark(schema.execute_sync, query, context_value={"allowed": True})
    assert result.errors is None
    assert result.data == (
        {"protected": 42}
        if operation == "permission"
        else {"checked": {"message": "invalid"}}
    )

from datetime import date
from enum import Enum
from typing import NewType

import pytest
from pytest_codspeed import BenchmarkFixture

import strawberry

Token = strawberry.scalar(
    NewType("Token", str),
    serialize=lambda value: f"token:{value}",
    parse_value=lambda value: value.removeprefix("token:"),
)


@strawberry.enum
class Role(Enum):
    USER = "user"
    ADMIN = "admin"


@strawberry.input
class Filter:
    ids: list[strawberry.ID]
    birthday: date
    token: Token
    role: Role = Role.USER
    label: str | None = "untitled"


@strawberry.input
class SearchInput:
    filter: Filter
    limit: int = 100


@strawberry.type
class Output:
    ids: list[strawberry.ID]
    birthday: date
    token: Token
    role: Role
    label: str | None


@strawberry.type
class Query:
    @strawberry.field
    def echo(self, input: SearchInput) -> Output:
        return Output(
            ids=input.filter.ids[: input.limit],
            birthday=input.filter.birthday,
            token=input.filter.token,
            role=input.filter.role,
            label=input.filter.label,
        )


@pytest.mark.parametrize(
    "label",
    [{}, {"label": None}, {"label": "selected"}],
    ids=["omitted", "null", "value"],
)
def test_nested_inputs_and_scalars(benchmark: BenchmarkFixture, label: dict):
    schema = strawberry.Schema(query=Query)
    ids = [str(i) for i in range(100)]
    result = benchmark(
        schema.execute_sync,
        "query ($input: SearchInput!) { echo(input: $input) { ids birthday token role label } }",
        variable_values={
            "input": {
                "filter": {
                    "ids": ids,
                    "birthday": "2000-01-01",
                    "token": "token:example",
                    **label,
                }
            }
        },
    )
    assert result.errors is None
    assert result.data == {
        "echo": {
            "ids": ids,
            "birthday": "2000-01-01",
            "token": "token:example",
            "role": "USER",
            "label": label.get("label", "untitled"),
        }
    }

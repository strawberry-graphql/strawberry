from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


CODE = """
from typing import Any

import strawberry
from strawberry.types.info import Info


@strawberry.type
class Fruit:
    name: str
    color: str


@strawberry.type
class Query:
    @strawberry.input_mutation
    def create_fruit(
        self,
        info: Info[Any, Any],
        name: str,
        color: str,
    ) -> Fruit:
        ...

    @strawberry.input_mutation
    async def create_fruit_async(
        self,
        info: Info[Any, Any],
        name: str,
        color: str,
    ) -> Fruit:
        ...


reveal_type(Query.create_fruit)
reveal_type(Query.create_fruit_async)
"""


def test_input_mutation_no_errors():
    results = run_pyright(CODE)
    assert results == [
        Result(
            type="information",
            message='Type of "Query.create_fruit" is "Any"',
            line=35,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Query.create_fruit_async" is "Any"',
            line=36,
            column=13,
        ),
    ]

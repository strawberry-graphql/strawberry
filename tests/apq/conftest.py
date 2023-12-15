import pytest

import strawberry
from strawberry.schema.config import StrawberryConfig


@pytest.fixture
def simple_schema() -> strawberry.Schema:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello_world(self) -> str:
            return "hi"

    return strawberry.Schema(query=Query, config=StrawberryConfig(use_apq=True))

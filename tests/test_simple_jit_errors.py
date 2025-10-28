"""
Simple test to verify basic error handling in JIT.
"""

from typing import Optional

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class TestType:
    @strawberry.field
    def working_field(self) -> str:
        return "working"

    @strawberry.field
    def error_field(self) -> Optional[str]:
        raise Exception("Test error")


@strawberry.type
class Query:
    @strawberry.field
    def test(self) -> TestType:
        return TestType()


def test_basic_error_handling():
    schema = strawberry.Schema(Query)

    query = """
    query {
        test {
            workingField
            errorField
        }
    }
    """

    # Standard execution handles errors
    execute_sync(schema._schema, parse(query), root_value=Query())

    # JIT should handle errors too - they should be in the result, not raised
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query())
    # Errors should be in the result
    assert jit_result.get("errors") is not None


if __name__ == "__main__":
    test_basic_error_handling()

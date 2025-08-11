"""
Simple test to verify basic error handling in JIT.
"""

import strawberry
from typing import Optional
from graphql import execute_sync, parse
from strawberry.jit_compiler import compile_query


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
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    print("Standard result:", result.data)
    print("Standard errors:", result.errors)
    
    # JIT should handle errors too
    try:
        compiled_fn = compile_query(schema._schema, query)
        jit_result = compiled_fn(Query())
        print("JIT result:", jit_result)
    except Exception as e:
        print("JIT error:", e)
        print("JIT should handle errors internally, not raise them!")


if __name__ == "__main__":
    test_basic_error_handling()
"""Debug error handling in JIT compiler."""

import strawberry
from typing import Optional
from graphql import execute_sync, parse
from strawberry.jit_compiler import compile_query


@strawberry.type
class ErrorParent:
    id: int
    
    @strawberry.field
    def nullable_item(self) -> Optional[str]:
        """Nullable field that errors."""
        raise Exception("Error in nullable field")
    
    @strawberry.field
    def non_nullable_item(self) -> str:
        """Non-nullable field that errors."""
        raise Exception("Error in non-nullable field")


@strawberry.type
class Query:
    @strawberry.field
    def parent(self) -> ErrorParent:
        return ErrorParent(id=1)


def test_nullable_field():
    """Test nullable field error handling."""
    schema = strawberry.Schema(Query)
    
    query = """
    query {
        parent {
            id
            nullableItem
        }
    }
    """
    
    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    print("Standard result (nullable):")
    print("  Data:", result.data)
    print("  Errors:", len(result.errors) if result.errors else 0)
    
    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    jit_result = compiled_fn(Query())
    print("\nJIT result (nullable):")
    print("  Result:", jit_result)
    
    # Check if they match
    if isinstance(jit_result, dict):
        if "data" in jit_result:
            print("  Has data key:", jit_result.get("data"))
            print("  Has errors key:", "errors" in jit_result)
        else:
            print("  Direct result (no data/errors wrapper)")
    
    print("\n" + "="*50)


def test_non_nullable_field():
    """Test non-nullable field error handling."""
    schema = strawberry.Schema(Query)
    
    query = """
    query {
        parent {
            id
            nonNullableItem
        }
    }
    """
    
    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    print("\nStandard result (non-nullable):")
    print("  Data:", result.data)
    print("  Errors:", len(result.errors) if result.errors else 0)
    
    # JIT execution
    try:
        compiled_fn = compile_query(schema._schema, query)
        jit_result = compiled_fn(Query())
        print("\nJIT result (non-nullable):")
        print("  Result:", jit_result)
    except Exception as e:
        print("\nJIT raised exception:", e)
    
    print("\n" + "="*50)


if __name__ == "__main__":
    test_nullable_field()
    test_non_nullable_field()
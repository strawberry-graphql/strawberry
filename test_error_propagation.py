"""Test non-nullable error propagation in JIT compiler."""

import strawberry
from typing import Optional
from graphql import execute_sync, parse
from strawberry.jit_compiler import compile_query


@strawberry.type
class DeepChild:
    value: str
    
    @strawberry.field
    def error_field(self) -> str:  # Non-nullable
        raise Exception("Deep error")
    
    @strawberry.field
    def safe_field(self) -> str:
        return "safe"


@strawberry.type
class MiddleChild:
    @strawberry.field
    def deep_child(self) -> DeepChild:  # Non-nullable
        return DeepChild(value="test")
    
    @strawberry.field
    def nullable_deep_child(self) -> Optional[DeepChild]:  # Nullable
        return DeepChild(value="nullable-test")


@strawberry.type
class Parent:
    @strawberry.field
    def middle_child(self) -> MiddleChild:  # Non-nullable
        return MiddleChild()
    
    @strawberry.field
    def id(self) -> int:
        return 1


@strawberry.type
class Query:
    @strawberry.field
    def parent(self) -> Optional[Parent]:  # Nullable at top
        return Parent()
    
    @strawberry.field
    def non_nullable_parent(self) -> Parent:  # Non-nullable at top
        return Parent()


def test_error_propagation_to_nullable_ancestor():
    """Test that errors propagate to first nullable ancestor."""
    schema = strawberry.Schema(Query)
    
    # Query with error in deep non-nullable chain
    query = """
    query {
        parent {
            id
            middleChild {
                deepChild {
                    value
                    errorField
                }
            }
        }
    }
    """
    
    print("Test 1: Error propagation to nullable ancestor")
    print("="*50)
    
    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    print("Standard result:")
    print("  Data:", result.data)
    print("  Errors:", len(result.errors) if result.errors else 0, "errors")
    if result.errors:
        print("  Error message:", result.errors[0].message)
        print("  Error path:", result.errors[0].path)
    
    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    jit_result = compiled_fn(Query())
    print("\nJIT result:")
    if isinstance(jit_result, dict) and "data" in jit_result:
        print("  Data:", jit_result["data"])
        print("  Errors:", len(jit_result.get("errors", [])), "errors")
        if jit_result.get("errors"):
            print("  Error message:", jit_result["errors"][0]["message"])
            print("  Error path:", jit_result["errors"][0]["path"])
    else:
        print("  Result:", jit_result)
    
    # Verify: entire parent should be nulled
    assert result.data == {"parent": None}, f"Expected parent to be null, got {result.data}"
    if isinstance(jit_result, dict) and "data" in jit_result:
        assert jit_result["data"] == {"parent": None}, f"JIT: Expected parent to be null, got {jit_result['data']}"
    
    print("\n✅ Test 1 passed: Error propagated to nullable ancestor\n")


def test_error_with_nullable_intermediate():
    """Test error handling when there's a nullable field in the chain."""
    schema = strawberry.Schema(Query)
    
    query = """
    query {
        parent {
            id
            middleChild {
                nullableDeepChild {
                    value
                    errorField
                }
            }
        }
    }
    """
    
    print("Test 2: Error with nullable intermediate field")
    print("="*50)
    
    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    print("Standard result:")
    print("  Data:", result.data)
    print("  Errors:", len(result.errors) if result.errors else 0, "errors")
    
    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    jit_result = compiled_fn(Query())
    print("\nJIT result:")
    if isinstance(jit_result, dict) and "data" in jit_result:
        print("  Data:", jit_result["data"])
        print("  Errors:", len(jit_result.get("errors", [])), "errors")
    
    # Verify: only the nullable field should be nulled, not the entire parent
    expected = {
        "parent": {
            "id": 1,
            "middleChild": {
                "nullableDeepChild": None  # Only this should be null
            }
        }
    }
    assert result.data == expected, f"Expected {expected}, got {result.data}"
    if isinstance(jit_result, dict) and "data" in jit_result:
        assert jit_result["data"] == expected, f"JIT: Expected {expected}, got {jit_result['data']}"
    
    print("\n✅ Test 2 passed: Error stopped at nullable intermediate\n")


def test_error_at_root_non_nullable():
    """Test error handling when root field is non-nullable."""
    schema = strawberry.Schema(Query)
    
    query = """
    query {
        nonNullableParent {
            middleChild {
                deepChild {
                    errorField
                }
            }
        }
    }
    """
    
    print("Test 3: Error with non-nullable root")
    print("="*50)
    
    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    print("Standard result:")
    print("  Data:", result.data)
    print("  Errors:", len(result.errors) if result.errors else 0, "errors")
    
    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    jit_result = compiled_fn(Query())
    print("\nJIT result:")
    if isinstance(jit_result, dict) and "data" in jit_result:
        print("  Data:", jit_result["data"])
        print("  Errors:", len(jit_result.get("errors", [])), "errors")
    
    # When root is non-nullable and has error, entire result should be null
    assert result.data is None, f"Expected None, got {result.data}"
    if isinstance(jit_result, dict) and "data" in jit_result:
        assert jit_result["data"] is None, f"JIT: Expected None, got {jit_result['data']}"
    
    print("\n✅ Test 3 passed: Error propagated all the way to root\n")


def test_mixed_errors_and_success():
    """Test partial success with some fields erroring."""
    schema = strawberry.Schema(Query)
    
    query = """
    query {
        parent {
            id
            middleChild {
                deepChild {
                    value
                    safeField
                }
                nullableDeepChild {
                    errorField
                }
            }
        }
    }
    """
    
    print("Test 4: Mixed errors and success")
    print("="*50)
    
    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    print("Standard result:")
    print("  Data:", result.data)
    print("  Errors:", len(result.errors) if result.errors else 0, "errors")
    
    # JIT execution
    compiled_fn = compile_query(schema._schema, query)
    jit_result = compiled_fn(Query())
    print("\nJIT result:")
    if isinstance(jit_result, dict) and "data" in jit_result:
        print("  Data:", jit_result["data"])
        print("  Errors:", len(jit_result.get("errors", [])), "errors")
    
    # Should have partial success
    expected = {
        "parent": {
            "id": 1,
            "middleChild": {
                "deepChild": {
                    "value": "test",
                    "safeField": "safe"
                },
                "nullableDeepChild": None  # This errors but is nullable
            }
        }
    }
    assert result.data == expected, f"Expected {expected}, got {result.data}"
    if isinstance(jit_result, dict) and "data" in jit_result:
        assert jit_result["data"] == expected, f"JIT: Expected {expected}, got {jit_result['data']}"
    
    print("\n✅ Test 4 passed: Partial success with nullable error\n")


if __name__ == "__main__":
    test_error_propagation_to_nullable_ancestor()
    test_error_with_nullable_intermediate()
    test_error_at_root_non_nullable()
    test_mixed_errors_and_success()
    
    print("="*50)
    print("✅ All non-nullable error propagation tests passed!")
    print("="*50)
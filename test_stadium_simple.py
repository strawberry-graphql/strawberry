"""Simple test without arguments to verify resolver integration works
"""


import strawberry_core_rs

import strawberry


@strawberry.type
class SimpleStadium:
    name: str
    capacity: int


@strawberry.type
class Query:
    @strawberry.field
    def stadium(self) -> SimpleStadium:
        print("[Python] stadium() called (no arguments)")
        return SimpleStadium(name="Test Stadium", capacity=50000)


schema = strawberry.Schema(query=Query)
sdl = str(schema)
query_instance = Query()

query = """
{
    stadium {
        name
        capacity
    }
}
"""

print("Testing simple query without arguments...")
print()

try:
    result = strawberry_core_rs.execute_query_with_resolvers(sdl, query, query_instance)
    print("✅ Success!")
    print(result)
except Exception as e:
    print(f"❌ Error: {e}")

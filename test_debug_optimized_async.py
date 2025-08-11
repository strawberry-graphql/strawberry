"""Debug the optimized async JIT compiler."""
import asyncio
import strawberry
from strawberry.jit_compiler_optimized import OptimizedGraphQLJITCompiler


@strawberry.type
class AsyncPost:
    id: int
    title: str
    
    @strawberry.field
    async def content(self) -> str:
        await asyncio.sleep(0.01)
        return f"Content for {self.title}"


@strawberry.type
class AsyncAuthor:
    id: int
    name: str
    
    @strawberry.field
    async def bio(self) -> str:
        await asyncio.sleep(0.01)
        return f"Bio for {self.name}"


@strawberry.type
class AsyncQuery:
    @strawberry.field
    async def author(self, id: int) -> AsyncAuthor:
        await asyncio.sleep(0.01)
        return AsyncAuthor(id=id, name=f"Author {id}")


async def main():
    schema = strawberry.Schema(AsyncQuery)
    
    query = """
    query {
        author(id: 1) {
            id
            name
            bio
        }
    }
    """
    
    compiler = OptimizedGraphQLJITCompiler(schema._schema)
    compiler.compile_query(query)
    
    print("Generated code:")
    print("=" * 60)
    print("\n".join(compiler.generated_code))
    print("=" * 60)
    
    # Try to compile and run
    compiled_fn = compiler.compile_query(query)
    root = AsyncQuery()
    
    result = await compiled_fn(root)
    print("\nResult:", result)


if __name__ == "__main__":
    asyncio.run(main())
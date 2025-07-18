import asyncio  # noqa: INP001
import random

import strawberry
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Author:
    id: strawberry.ID
    name: str


@strawberry.type
class Comment:
    id: strawberry.ID
    content: str

    @strawberry.field
    async def author(self) -> Author:
        await asyncio.sleep(random.randint(0, 2))  # noqa: S311
        return Author(id=strawberry.ID("Author:1"), name="John Doe")


@strawberry.type
class BlogPost:
    id: strawberry.ID
    title: str
    content: str

    @strawberry.field
    async def comments(self) -> strawberry.Streamable[Comment]:
        for x in range(5):
            await asyncio.sleep(random.choice([0, 0.5, 1, 1.5, 2]))  # noqa: S311

            yield Comment(id=strawberry.ID(f"Comment:{x}"), content="Great post!")


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self, delay: float = 0) -> str:
        await asyncio.sleep(delay)
        return "Hello, world!"

    @strawberry.field
    async def blog_post(self, id: strawberry.ID) -> BlogPost:
        return BlogPost(id=id, title="My Blog Post", content="This is my blog post.")


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        enable_experimental_incremental_execution=True,
    ),
)

import asyncio  # noqa: INP001

import strawberry
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Comment:
    id: strawberry.ID
    content: str


@strawberry.type
class BlogPost:
    id: strawberry.ID
    title: str
    content: str

    @strawberry.field
    async def comments(self) -> list[Comment]:
        await asyncio.sleep(4)

        return [
            Comment(id=strawberry.ID("1"), content="Great post!"),
            Comment(id=strawberry.ID("2"), content="Thanks for sharing!"),
        ]


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

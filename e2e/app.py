import asyncio  # noqa: INP001
import random
from collections.abc import AsyncGenerator

from fastapi import FastAPI

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.schema.config import StrawberryConfig
from strawberry.subscriptions import (
    GRAPHQL_SSE_PROTOCOL,
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
    MULTIPART_SUBSCRIPTION_PROTOCOL,
)


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
        await asyncio.sleep(random.uniform(0, 0.5))  # noqa: S311
        return Author(id=strawberry.ID("Author:1"), name="John Doe")


@strawberry.type
class BlogPost:
    id: strawberry.ID
    title: str
    content: str

    @strawberry.field
    async def comments(self) -> strawberry.Streamable[Comment]:
        for x in range(5):
            await asyncio.sleep(random.uniform(0, 0.5))  # noqa: S311

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

    @strawberry.field
    async def failing(self) -> str:
        raise ValueError("Query failed")


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def echo(self, message: str) -> str:
        return message


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 3) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i

    @strawberry.subscription
    async def count_then_fail(self, target: int = 2) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i

        raise ValueError("Subscription failed")

    @strawberry.subscription
    async def resumable_count(
        self, info: strawberry.Info, target: int = 3
    ) -> AsyncGenerator[int, None]:
        # SSE uses normal HTTP requests, so the Last-Event-ID header is read from
        # the request that's already in the context. Strawberry never replays on
        # its own, so the resolver decides where to resume from.
        last_event_id = info.context["request"].headers.get("last-event-id")
        start = int(last_event_id) + 1 if last_event_id is not None else 0

        for i in range(start, target):
            yield i


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(
        enable_experimental_incremental_execution=True,
    ),
)

subscription_protocols = (
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
    MULTIPART_SUBSCRIPTION_PROTOCOL,
    GRAPHQL_SSE_PROTOCOL,
)


app = FastAPI()
app.include_router(
    GraphQLRouter(schema, path="/", subscription_protocols=subscription_protocols)
)
app.include_router(
    GraphQLRouter(schema, subscription_protocols=subscription_protocols),
    prefix="/graphql",
)

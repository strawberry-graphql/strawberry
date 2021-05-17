Release type: minor

This release adds support for GraphQL subscriptions to the AIOHTTP integration.
Subscription support works out of the box and does not require any additional
configuration.

Here is an example how to get started with subscriptions in general. Note that by
specification GraphQL schemas must always define a query, even if only subscriptions
are used.

```python
import asyncio
import typing
import strawberry


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> typing.AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)


@strawberry.type
class Query:
    @strawberry.field
    def _unused(self) -> None:
        pass


schema = strawberry.Schema(subscription=Subscription, query=Query)
```

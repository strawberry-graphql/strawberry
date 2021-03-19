---
title: Async
---

# Async

Async is a concurrent programming design that has been supported since Python
3.4 to learn more about async in python refer to
[Real Python’s Async walkthrough](https://realpython.com/async-io-python/).

Strawberry supports both async and non async resolvers, so can mix and match
them in your code. Here’s an example of async resolver:

```python
import asyncio
import strawberry


async def resolve_hello(root) -> str:
    await asyncio.sleep(1)

    return "Hello world"


@strawberry.type
class Query:
    hello: str = strawberry.field(resolver=resolve_hello)


schema = strawberry.Schema(Query)
```

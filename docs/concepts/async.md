---
title: Async
---

# Async

Async is a concurrent programming design that has been supported in Python since
version 3.4. To learn more about async in Python refer to
[Real Python’s Async walkthrough](https://realpython.com/async-io-python/).

Strawberry supports both async and non async resolvers, so you can mix and match
them in your code. Here’s an example of an async resolver:

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

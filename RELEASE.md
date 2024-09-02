Release type: minor

Support for schema-extensions in subscriptions.

i.e:

```python
import asyncio
from typing import AsyncIterator

import strawberry
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types.execution import PreExecutionError


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def notifications(self, info: strawberry.Info) -> AsyncIterator[str]:
        for _ in range(3):
            yield "!dlrow ,olleH"


class MyExtension(SchemaExtension):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = 0

    async def on_operation(self):
        # This would run when the subscription starts
        print("Subscription started")
        yield
        # The subscription has ended
        print("Subscription ended")

    # Other hooks are the same as in normal execution.
    async def resolve(self, _next, root, info, *args, **kwargs):
        res = _next(root, info, *args, **kwargs)
        return res[::-1]


schema = strawberry.Schema(
    query=Query, subscription=Subscription, extensions=[MyExtension]
)


async def main():
    agen = await schema.subscribe("subscription { notifications }")
    if isinstance(agen, PreExecutionError):
        print("this is an initial execution error.")
        print(agen.errors)
    else:
        async for res in agen:
            print(res.data)


asyncio.run(main())
```

Should output this

```console
Subscription started
before yield 0
after yield 0
before yield 1
after yield 1
{'notifications': 'Hello, world!'}
before yield 2
after yield 2
{'notifications': 'Hello, world!'}
before yield 3
after yield 3
{'notifications': 'Hello, world!'}
before yield 4
after yield 4
Subscription ended
```

### Breaking changes

This release also updates the signature of `Schema.subscribe`. From:

```py
async def subscribe(
    self,
    query: str,
    variable_values: Optional[Dict[str, Any]] = None,
    context_value: Optional[Any] = None,
    root_value: Optional[Any] = None,
    operation_name: Optional[str] = None,
) -> Union[AsyncIterator[GraphQLExecutionResult], GraphQLExecutionResult]:
```

To:

```py
async def subscribe(
    self,
    query: Optional[str],
    variable_values: Optional[Dict[str, Any]] = None,
    context_value: Optional[Any] = None,
    root_value: Optional[Any] = None,
    operation_name: Optional[str] = None,
) -> Union[AsyncGenerator[ExecutionResult, None], PreExecutionError]:
```

Due to moving away from graphql-core result types to our internal types.

Release type: patch

This release introduces `strawberry.subscription_result(...)` function for make result type of subscription.
It makes another way to declare subscription resolver's result type.

```python
import strawberry


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def time(self) -> strawberry.subscription_result(str):
        # same as AsyncGenerator[str, None]
        pass
```

Release type: patch

This releases improves how we handle Annotated and async types
(used in subscriptions). Previously we weren't able to use
unions with names inside subscriptions, now that's fixed 😊

Example:

```python
@strawberry.type
class A:
    a: str


@strawberry.type
class B:
    b: str


@strawberry.type
class Query:
    x: str = "Hello"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def example_with_union(self) -> AsyncGenerator[Union[A, B], None]:
        yield A(a="Hi")
```

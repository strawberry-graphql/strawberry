Release type: minor

This release updates the API to listen to Django Channels to avoid race conditions
when confirming GraphQL subscriptions.

**Breaking changes:**

This release contains a breaking change for the Channels integration. The
`channel_listen` method is now an async context manager that returns an awaitable
AsyncGenerator.

An example of migrating existing code is given below:

```py
# Existing code

@strawberry.type
class MyDataType:
   name: str

@strawberry.type
class Subscription:
   @strawberry.subscription
   async def my_data_subscription(
      self, info: Info, groups: list[str]
   ) -> AsyncGenerator[MyDataType | None, None]:
      yield None
      async for message in info.context["ws"].channel_listen("my_data", groups=groups):
         yield MyDataType(name=message["payload"])
```

```py
# New code

@strawberry.type
class Subscription:
   @strawberry.subscription
   async def my_data_subscription(
      self, info: Info, groups: list[str]
   ) -> AsyncGenerator[MyDataType | None, None]:
      async with info.context["ws"].channel_listen("my_data", groups=groups) as cm:
         yield None
         async for message in cm:
            yield MyDataType(name=message["payload"])
```
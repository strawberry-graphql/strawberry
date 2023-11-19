Release type: minor

Fixes generic type arguments for Coroutine in RESOLVER_TYPE. Async resolvers will now be typed-checked correctly when passed as `strawberry.field(resolver=resolver_func)`.

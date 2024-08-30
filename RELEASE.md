Release type: patch

Fix an issue where `StrawberryResolver.is_async` was returning `False` for a
function decorated with asgiref's `@sync_to_async`.

The root cause is that in python >= 3.12 coroutine functions are market using
`inspect.markcoroutinefunction`, which should be checked with
`inspect.iscoroutinefunction` instead of `asyncio.iscoroutinefunction`

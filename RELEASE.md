Release type: patch

Fix a bug "StrawberryResolver.is_async returns False for a function decorated by
@sync_to_async".

The root cause is that in python >= 3.12 coroutine functions are market using
`inspect.markcoroutinefunction`, which should be checked with
`inspect.iscoroutinefunction` instead of `asyncio.iscoroutinefunction`

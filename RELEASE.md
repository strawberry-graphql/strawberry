Release type: patch

Fix a bug "StrawberryResolver.is_async returns False for a function decorated by @sync_to_async"
The root cause was inspect.iscoroutinefunction() function returns True only for functions defined with "async def" in python < 3.12

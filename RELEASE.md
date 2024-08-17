Release type: patch

Fix a bug "a custom resolver with permission_classes doesn't accept @sync_to_async decorator"
The root cause was inspect.iscoroutinefunction() function returns True only for functions defined with "async def".

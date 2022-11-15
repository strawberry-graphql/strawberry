Release type: patch

This release changes the dataloader batch resolution to avoid resolving
futures that were canceled, and also from reusing them from the cache.
Trying to resolve a future that was canceled would raise `asyncio.InvalidStateError`

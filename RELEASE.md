Release type: patch

This release fixes a TypeError on Python 3.8 due to us using a
`asyncio.Queue[Tuple[bool, Any]](1)` instead of `asyncio.Queue(1)`.

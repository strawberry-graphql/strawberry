Release type: patch

This release fixes a bug in `_listen_to_channel_generator` where `yield await
awaitable` inside `try/except asyncio.TimeoutError` caused the `yield` to fall
within the `try` block's bytecode exception table range.

This meant that a `TimeoutError` thrown into the generator at the `yield` point
(i.e. when the generator is suspended after delivering a value) was incorrectly
caught by the internal timeout handler, silently stopping the generator instead
of propagating to the caller. In production, this could manifest as
`RuntimeError: cannot reuse already awaited coroutine` during WebSocket
disconnect cleanup.

The fix splits `yield await awaitable` into `result = await awaitable` followed
by `yield result`, so the `yield` is outside the `try` block and exceptions
thrown at the yield point propagate correctly.

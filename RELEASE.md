Release type: patch

Fixed a race condition in `AsyncBaseHTTPView._stream_with_heartbeat` that could cause the final multipart boundary to be lost in subscription responses. This race condition resulted in malformed HTTP responses where clients would wait until timeout, as the response was never properly terminated per RFC 2046 multipart/mixed specification.

The fix ensures that the closing boundary (`--graphql--`) is always present in multipart responses, even when the race condition causes the final boundary chunk to remain in the queue when the drain task completes.

This particularly affected subscriptions under high system load or with fast-yielding generators, where the timing of asyncio task scheduling could cause `task.done()` to return `True` before the final boundary was retrieved from the queue.

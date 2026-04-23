---
release type: minor
---

Cancel DataLoader dispatch task when all futures are cancelled.

Previously, the background task created by `dispatch()` was fire-and-forget — its
reference was never stored, so it couldn't be cancelled even when no caller was
waiting for the results. This caused wasted work (e.g. database queries against
closed sessions) when using `asyncio.TaskGroup` or similar structured concurrency
patterns that cancel futures on failure.

The dispatch task is now tracked in `Batch._dispatch_task` and automatically
cancelled when all futures in the batch are cancelled.

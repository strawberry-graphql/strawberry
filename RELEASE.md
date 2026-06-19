---
release type: minor
---

This release adds a shared internal HTTP stream transport for multipart
subscription responses.

Application behavior for multipart subscriptions is largely unchanged. The
shared transport now owns multipart response headers, heartbeat frames,
completion frames, batching errors, and sync-mode errors, keeping Strawberry's
built-in HTTP integrations on the same streaming contract.

The one behavioral change is that each multipart part's `Content-Length` is now
computed from the UTF-8 byte length of the payload instead of its character
count, fixing the header for responses containing non-ASCII data.

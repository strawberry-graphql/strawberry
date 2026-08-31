---
release type: patch
social_messages:
  x: >-
    Strawberry {version} is out! This release fixes a permission bypass where a
    sync `has_permission` returning an awaitable could grant access to protected
    fields. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    Strawberry {version} is out. This release fixes a permission bypass
    (GHSA-pfvf-fwfp-25mp) where a synchronous `has_permission` that returned an
    awaitable could unintentionally grant access to protected fields. The
    synchronous permission path now fails closed with a clear error.
---

This release fixes a permission bypass (GHSA-pfvf-fwfp-25mp) where a custom
permission could unintentionally authorize access to a protected field.

When a permission's `has_permission` was a normal `def` that returned an
awaitable (for example a wrapper returning a coroutine), Strawberry classified
the permission as synchronous because only `async def` methods are detected as
async. On the synchronous resolve path the returned awaitable was evaluated for
truthiness directly, and an awaitable is always truthy — so the check passed and
the protected resolver ran even when the awaitable resolved to `False`. This
affected any field with a synchronous resolver, under both `execute_sync` and
`execute`.

Strawberry now detects this case and fails closed: the synchronous permission
path raises a clear error instead of trusting the awaitable, so access is never
granted by accident. Permissions written as `async def has_permission` continue
to work as before. If you intend a permission to be asynchronous, declare it
with `async def` (or return a plain boolean from a synchronous one).

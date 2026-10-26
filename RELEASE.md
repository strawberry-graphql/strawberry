---
release type: minor
social_messages:
  x: >-
    Strawberry {version} is out! Permissions must now return a boolean, which
    fixes a bypass where a `has_permission` returning an async generator could
    grant access to protected fields. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    Strawberry {version} is out. Permission classes must now return a boolean
    from `has_permission`. This fixes a permission bypass where a result
    Strawberry could not evaluate, such as an async generator, was treated as
    granting access. Non-boolean results now fail closed with a clear error.
---

This release fixes a permission bypass where a custom permission could
unintentionally authorize access to a protected field, by requiring
`has_permission` to return a boolean.

When `has_permission` was written as an async generator (an `async def`
containing `yield`), or returned a generator, async generator, or similar
object, Strawberry evaluated the returned object for truthiness. These objects
are always truthy and slipped past the check for awaitables added in 0.326.1,
so the protected resolver ran even when the permission meant to deny access.
This affected queries and mutations under both `execute_sync` and `execute`.

Strawberry now only grants access when `has_permission` returns (or resolves
to) `True`, and denies it when it returns `False`. Any other value raises a
`PermissionReturnedNonBooleanError`, even with `fail_silently=True`.

This is a breaking change for permissions that return other truthy or falsy
values, such as a user object or `None`:

```python
# Before
def has_permission(self, source, info, **kwargs):
    return info.context.user


# After
def has_permission(self, source, info, **kwargs) -> bool:
    return bool(info.context.user)
```

See the [breaking changes guide](https://strawberry.rocks/docs/breaking-changes/0.338.0)
for more details.

---
release type: patch
---

This release fixes schema printing for input object defaults that explicitly set
nullable fields to `null`.

Strawberry now preserves explicit `None` values in printed nested input
defaults, including fields set with `strawberry.Some(None)` and fields renamed
with `strawberry.field(name=...)`, while still omitting fields that were not
explicitly set.

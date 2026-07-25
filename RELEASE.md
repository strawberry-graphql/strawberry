---
release type: patch
social_messages:
  x: >-
    🍓 Strawberry {version} is out! This release fixes type checkers rejecting
    custom comparison methods like __gt__ on Strawberry types.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    Strawberry {version} is out. This release fixes type checkers incorrectly
    rejecting custom comparison methods such as __gt__ on Strawberry types,
    which are not ordered dataclasses.
---

This release fixes type checkers incorrectly rejecting custom comparison
methods on Strawberry types.

The `type`, `input`, `interface` and federation decorators declared
`order_default=True` in their `dataclass_transform`, so type checkers assumed an
auto-generated ordering and flagged a user-defined `__gt__` (or another rich
comparison method) as conflicting. Strawberry builds these dataclasses without
`order`, so this is now `order_default=False` and defining your own comparison
operators no longer raises a false positive.

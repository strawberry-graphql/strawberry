---
release type: patch
---

This release fixes generic `@strawberry.interface` types with generic fields and generic field arguments on specialized types.

Strawberry now specializes generic interfaces when implemented or extended with concrete type arguments, and resolves generic field argument types (both during schema construction and at runtime) for specialized subclasses and generic interfaces.

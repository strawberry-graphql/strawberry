---
release type: patch
---

Fix `scalar_map` not being applied to pydantic model fields during schema
generation. Previously, `NewType` wrappers on pydantic fields were
unconditionally unwrapped to their underlying type (e.g. `str`) during
pydantic type resolution, which destroyed the type identity before the
`scalar_map` from `StrawberryConfig` could intercept it at schema
construction time.

This change removes the early `NewType` unwrapping in the pydantic compat
layer and instead adds `__supertype__` fallback logic to `is_scalar()` and
`from_scalar()`, so that:
- `NewType` annotations in `scalar_map` are matched correctly (the fix)
- `NewType` fields without a `scalar_map` entry still resolve to their
  underlying type via the new fallback (backward compatible)

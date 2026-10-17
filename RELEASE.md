---
release type: minor
---

This release adds an internal `specialize` hook to `StrawberryObjectDefinition`.
The upcoming first-class Pydantic integration uses it to support generic models
used directly, like `Page[User]`.

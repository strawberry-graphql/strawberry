---
release type: patch
---

This release fixes `StrawberryConfig(default_resolver=...)` not working with `@strawberry.experimental.pydantic.type` when resolvers return non-model objects such as `dict`s, by no longer unconditionally injecting an `is_type_of` check on experimental Pydantic object types while preserving Pydantic model resolution for interfaces and unions.

---
release type: patch
---

This release fixes query code generation producing different type orders across
Python versions.

Strawberry now visits collected types in order and emits each type after its
dependencies. This makes generated output consistent across supported Python
versions.

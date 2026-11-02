---
release type: patch
---

This release fixes query code generation producing different type orders across
Python versions.

Generated types are emitted in collection order, with variable types collected
after their dependencies. This keeps generated output consistent across supported
Python versions.

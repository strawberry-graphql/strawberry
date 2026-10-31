---
release type: patch
---

This release fixes query code generation producing different type orders across
Python versions.

Generated types now appear after their dependencies, preserving collection order
among types whose dependencies have already been emitted. This makes generated
output consistent across supported Python versions.

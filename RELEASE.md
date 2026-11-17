---
release type: minor
---

This release adds a `--shared-fragments` option to `strawberry codegen`.

With the python plugin, fragment classes (and the types they depend on) are
written once to `fragments.py` and imported by each operation module, so the
same fragment is the same class across modules.

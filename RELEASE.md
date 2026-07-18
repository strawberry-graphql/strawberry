release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! It removes the deprecated `Extension`
    alias in favor of `SchemaExtension`. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release removes the deprecated
    `Extension` import alias from `strawberry.extensions`, completing a
    deprecation that started in 0.160.0 — use `SchemaExtension` instead.

This release removes the deprecated `Extension` import alias from `strawberry.extensions`, deprecated since [0.160.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.160.0). Use `SchemaExtension` instead.

### Migration guide

**Before (deprecated):**
```python
from strawberry.extensions import Extension


class MyExtension(Extension): ...
```

**After:**
```python
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension): ...
```

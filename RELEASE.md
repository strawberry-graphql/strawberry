Release type: minor

Remove deprecated `Extension` import alias from `strawberry.extensions`, deprecated since [0.160.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.160.0).

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

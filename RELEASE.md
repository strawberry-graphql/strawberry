Release type: minor

Remove deprecated `is_unset()` function, deprecated since [0.109.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.109.0).

### Migration guide

**Before (deprecated):**
```python
from strawberry.types.unset import is_unset

if is_unset(value):
    ...
```

**After:**
```python
from strawberry import UNSET

if value is UNSET:
    ...
```

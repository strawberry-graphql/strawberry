Release type: minor

Remove deprecated `LazyType["Name", "module"]` syntax, deprecated since [0.129.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.129.0).

### Migration guide

**Before (deprecated):**
```python
from strawberry.lazy_type import LazyType


@strawberry.type
class Query:
    user: LazyType["User", "myapp.types"]
```

**After:**
```python
from typing import Annotated
import strawberry


@strawberry.type
class Query:
    user: Annotated["User", strawberry.lazy("myapp.types")]
```

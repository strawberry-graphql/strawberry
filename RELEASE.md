Release type: minor

Remove deprecated `types` parameter from `strawberry.union()`, deprecated since [0.191.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.191.0).

You can run `strawberry upgrade annotated-union <path>` to automatically migrate your code.

### Migration guide

**Before (deprecated):**
```python
import strawberry

MyUnion = strawberry.union("MyUnion", types=(TypeA, TypeB))
```

**After:**
```python
from typing import Annotated
import strawberry

MyUnion = Annotated[TypeA | TypeB, strawberry.union("MyUnion")]
```

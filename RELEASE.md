Release type: minor

Remove deprecated `strawberry.scalar(cls, ...)` wrapper pattern and `ScalarWrapper`, deprecated since [0.288.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.288.0).

You can run `strawberry upgrade replace-scalar-wrappers <path>` to automatically replace built-in scalar wrapper imports.

### Migration guide

**Before (deprecated):**
```python
import strawberry
from datetime import datetime

EpochDateTime = strawberry.scalar(
    datetime,
    serialize=lambda v: int(v.timestamp()),
    parse_value=lambda v: datetime.fromtimestamp(v),
)


@strawberry.type
class Query:
    created: EpochDateTime
```

**After:**
```python
import strawberry
from typing import NewType
from datetime import datetime
from strawberry.schema.config import StrawberryConfig

EpochDateTime = NewType("EpochDateTime", datetime)


@strawberry.type
class Query:
    created: datetime


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        scalar_map={
            EpochDateTime: strawberry.scalar(
                name="EpochDateTime",
                serialize=lambda v: int(v.timestamp()),
                parse_value=lambda v: datetime.fromtimestamp(v),
            )
        }
    ),
)
```

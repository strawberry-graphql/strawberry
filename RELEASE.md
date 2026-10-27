---
release type: minor
---

This release adds custom scalar definitions through `Annotated`, without requiring
schema registration, and removes the deprecated `strawberry.scalar(cls, ...)`
wrapper pattern and `ScalarWrapper`, deprecated since
[0.288.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.288.0).

The decorator form is also removed. Custom scalars must have an explicit name.
Use `Annotated[PythonType, strawberry.scalar(name=..., ...)]` for a self-contained
scalar, or keep `StrawberryConfig.scalar_map` for existing Python types and
schema-wide overrides. Explicit mappings take precedence over annotated
definitions, which take precedence over built-ins. Mappings can target either
the annotated alias or its underlying Python type; alias-specific mappings win.

Schema code generation now emits annotated aliases, imports JSON from
`strawberry.scalars`, and preserves scalar metadata even when generating SDL
fragments without a schema root.

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
from typing import Annotated, NewType
from datetime import datetime, timezone

EpochValue = NewType("EpochValue", datetime)
EpochDateTime = Annotated[
    EpochValue,
    strawberry.scalar(
        name="EpochDateTime",
        serialize=lambda v: int(v.timestamp()),
        parse_value=lambda v: datetime.fromtimestamp(v, timezone.utc),
    ),
]


@strawberry.type
class Query:
    created: EpochDateTime


schema = strawberry.Schema(query=Query)
```

Declare the `NewType` separately so type checkers recognize it. Use
`scalar_map={datetime: definition}` to support existing `datetime` annotations
without updating them, or `scalar_map={EpochDateTime: definition}` to override
only this alias. For built-in JSON overrides, use `strawberry.scalars.JSON` as
the mapping key.

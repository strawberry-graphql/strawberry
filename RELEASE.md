Release type: minor

This release adds support for typing `JSON` values. For example, the following
can now be used to get better typing support on it:

```python
from typing import TypedDict
import strawberry
from strawberry.scalars import JSON


class SomeJSON(TypedDict):
    foo: int
    bar: str


@strawberry.type
class SomeType:
    json: JSON[SomeJSON]
```

Note that the scalar will still be exposed as `JSON` in the schema and strawberry
will not validate its value at runtime.

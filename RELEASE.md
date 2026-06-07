Release type: minor

`scalar_overrides` now matches generic `dict` annotations by their origin as a
fallback, so registering a bare `dict` covers every `dict[K, V]`
parameterization instead of needing one entry per variant.

Before, registering only the unparameterized origin (`dict`) did not match
parameterized annotations like `dict[str, int]`. You had to register the exact
annotation, and any other shape such as `dict[str, list[int]]` raised
`Unexpected type`:

```python
from typing import Any

import strawberry
from strawberry.scalars import JSON


@strawberry.type
class Query:
    settings: dict[str, Any]
    metadata: dict[str, list[int]]


schema = strawberry.Schema(
    query=Query,
    scalar_overrides={dict[str, Any]: JSON},
)
```

Now registering the unparameterized `dict` covers all of its parameterizations,
including resolver and mutation arguments typed with `dict[...]`. This is
especially useful for `strawberry.experimental.pydantic` models with typed
dictionary fields. Lookup still tries an exact match first, so existing overrides
keep working unchanged.

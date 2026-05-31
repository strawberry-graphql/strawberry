Release type: minor

`scalar_overrides` now matches generic containers by their origin as a
fallback, so registering a bare `dict` covers every `dict[K, V]`
parameterization instead of needing one entry per variant.

Before, a schema like this only worked if you registered the exact
annotation (`dict[str, Any]`), and any other shape such as
`dict[str, Optional[int]]` raised `Unexpected type`:

```python
import strawberry
from strawberry.scalars import JSON

@strawberry.type
class Query:
    settings: dict[str, int]
    metadata: dict[str, list[str]]

schema = strawberry.Schema(
    query=Query,
    scalar_overrides={dict: JSON},
)
```

Now registering the unparameterized `dict` (or `list`, etc.) covers all
of its parameterizations. Lookup still tries an exact match first, so
existing overrides keep working unchanged.

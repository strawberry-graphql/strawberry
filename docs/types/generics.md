---
title: Generics
---

# Generics

## JSONScalar

```
import json
from typing import Any, NewType

import strawberry

JSONScalar = strawberry.scalar(
    NewType("JSONScalar", Any),
    serialize=lambda v: v,
    parse_value=lambda v: json.loads(v),
    description="The GenericScalar scalar type represents a generic GraphQL scalar value that could be: List or Object."
)

```

Usage
```
@strawberry.type
class Query:
    @strawberry.field
    def data(self, info) -> GenericScalar:
        return {"hello": {"a": 1}, "someNumbers": [1, 2, 3]}

```

Query
```
query ExampleDataQuery {
  data
}
```

Returns
```
"data": {
  "hello": {
    "a": 1
   },
   "someNumbers": [1,2, 3]
},
```

Release type: patch

This release fixes an issue related to using `typing.Annotated` in resolver
arguments following the declaration of a reserved argument such as
`strawberry.types.Info`.

Before this fix, the following would be converted incorrectly:

```python
from __future__ import annotations
import strawberry
import uuid
from typing_extensions import Annotated
from strawberry.types import Info


@strawberry.type
class Query:
    @strawberry.field
    def get_testing(
        self,
        info: Info[None, None],
        id_: Annotated[uuid.UUID, strawberry.argument(name="id")],
    ) -> str | None:
        return None


schema = strawberry.Schema(query=Query)

print(schema)
```

Resulting in the schema:

```graphql
type Query {
  getTesting(id_: UUID!): String # ⬅️ see `id_`
}

scalar UUID
```

After this fix, the schema is converted correctly:

```graphql
type Query {
  getTesting(id: UUID!): String
}

scalar UUID
```

---
title: Pydantic Error Extension
summary:
  Formats Pydantic validation errors into structured GraphQL error extensions.
tags: pydantic,validation,errors,graphql,extensions
---

# `PydanticErrorExtension`

This extension detects Pydantic validation errors during GraphQL execution and
formats them into structured `validation_errors` under the `extensions` field of
GraphQL errors.

## Usage example:

```python
import strawberry
from strawberry.extensions import PydanticErrorExtension


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, email: str) -> str:
        return email


schema = strawberry.Schema(
    mutation=Mutation,
    extensions=[
        PydanticErrorExtension(),
    ],
)
```

## API reference:

```python
class PydanticErrorExtension: ...
```

This extension does not require any arguments.

## More examples:

<details>
  <summary>Example validation error output</summary>

```json
{
  "errors": [
    {
      "message": "Validation error",
      "extensions": {
        "validation_errors": [
          {
            "field": "email",
            "message": "value is not a valid email"
          }
        ]
      }
    }
  ]
}
```

</details>

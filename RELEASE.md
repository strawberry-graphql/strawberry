Release type: minor

This release adds support for defining fields using the `Annotated` syntax. This provides an
alternative way to specify field metadata alongside the type annotation.

Example usage:

```python
from typing import Annotated

import strawberry


@strawberry.type
class Query:
    name: Annotated[str, strawberry.field(description="The name")]
    age: Annotated[int, strawberry.field(deprecation_reason="Use birthDate instead")]


@strawberry.input
class CreateUserInput:
    name: Annotated[str, strawberry.field(description="User's name")]
    email: Annotated[str, strawberry.field(description="User's email")]
```

This syntax works alongside the existing assignment syntax:

```python
@strawberry.type
class Query:
    # Both styles work
    field1: Annotated[str, strawberry.field(description="Using Annotated")]
    field2: str = strawberry.field(description="Using assignment")
```

All `strawberry.field()` options are supported including `description`, `name`,
`deprecation_reason`, `directives`, `metadata`, and `permission_classes`.

Release type: minor

This release improves `schema-codegen` for input types in two ways:

1. Nullable input fields now use `strawberry.Maybe[T | None]`, allowing them to
   be omitted when constructing the input type.

2. GraphQL default values on input fields are now generated as Python defaults.
   Supported value types: integers, floats, strings, booleans, null, enums, and
   lists. When a field also has a description (or other metadata), the default is
   passed via `strawberry.field(description=..., default=...)`.

Before:

```python
@strawberry.input
class CreateUserInput:
    name: str
    role: int | None  # required – TypeError with {}
    # default value "42" from schema was lost
```

After:

```python
@strawberry.input
class CreateUserInput:
    name: str
    role: strawberry.Maybe[int | None] = 42
```

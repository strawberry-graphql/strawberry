Release type: patch

This release fixes an issue where `schema-codegen` generated nullable input
fields without default values, causing `TypeError` when instantiating inputs
with empty `{}` or with only required fields.

Nullable input fields are now generated using `strawberry.Maybe[T | None]`,
which allows them to be omitted when constructing the input type.

Before:

```python
@strawberry.input
class HealthResultInput:
    some_number: int | None  # Required - causes TypeError with {}
```

After:

```python
@strawberry.input
class HealthResultInput:
    some_number: strawberry.Maybe[int | None]  # Optional - works with {}
```

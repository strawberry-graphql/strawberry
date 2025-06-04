Release type: minor

Added a new configuration option `_unsafe_disable_same_type_validation` that allows disabling the same type validation check in the schema converter. This is useful in cases where you need to have multiple type definitions with the same name in your schema.

Example:

```python
@strawberry.type(name="DuplicatedType")
class A:
    a: int


@strawberry.type(name="DuplicatedType")
class B:
    b: int


schema = strawberry.Schema(
    query=Query,
    types=[A, B],
    config=strawberry.StrawberryConfig(_unsafe_disable_same_type_validation=True),
)
```

Note: This is an unsafe option and should be used with caution as it bypasses a safety check in the schema converter.

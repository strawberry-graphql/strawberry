---
title: Convert to Dictionary
---

# Convert to Dictionary

Strawberry provides a utility function to convert a Strawberry object to a
dictionary.

You can use `strawberry.asdict(...)` function:

```python
@strawberry.type
class User:
    name: str
    age: int


# should be {"name": "Lorem", "age": 25}
user_dict = strawberry.asdict(User(name="Lorem", age=25))
```

## Handling of `Maybe` and `UNSET` values

When using [`Maybe`](../types/maybe.md) fields, `strawberry.asdict` unwraps the
value of that field, if present. `Maybe` fields set to `None` are excluded
entirely.

Fields set to `UNSET` are excluded entirely:

```python
@strawberry.input
class Input:
    field_a: Maybe[str | None]
    field_b: Maybe[str | None]
    field_c: Maybe[str | None]


# should be {"field_a": "hello"}
# `field_b` is excluded because it is a `Maybe` set to `None`;
# `field_c` is excluded because it is UNSET
input_dict = asdict(
    Input(
        field_a=Some("hello"),
        field_b=None,
        field_c=UNSET,
    )
)
```

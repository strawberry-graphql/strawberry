---
title: UNSET
---

# UNSET

<Warning>

`UNSET` is considered legacy. For new code, we recommend using
[`Maybe`](./maybe.md) instead, which provides better type safety and clearer
semantics for handling optional input fields.

</Warning>

`UNSET` is a sentinel value that can be used to represent an unset value in a
field or argument. Similar to `undefined` in JavaScript, this value can be used
to differentiate between a field that was not set and a field that was set to
`None` or `null`.

## Basic Usage

```python
import strawberry


@strawberry.input
class UpdateUserInput:
    name: str | None = strawberry.UNSET
    phone: str | None = strawberry.UNSET


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user(self, input: UpdateUserInput) -> User:
        if input.name is not strawberry.UNSET:
            user.name = input.name
        if input.phone is not strawberry.UNSET:
            user.phone = input.phone
        return user
```

## Checking for UNSET

Use identity comparison to check if a value is unset:

```python
# Correct way to check
if value is strawberry.UNSET:
    print("Value was not provided")

# Also correct
if value is not strawberry.UNSET:
    print(f"Value was provided: {value}")
```

<Note>

The `is_unset()` helper function has been deprecated. Use
`value is strawberry.UNSET` instead.

</Note>

## Limitations

`UNSET` has some limitations compared to `Maybe`:

1. **Type Safety**: `UNSET` doesn't work well with type checkers since it's
   typed as `Any`
2. **Ambiguous Null Handling**: With `field: str | None = UNSET`, it's not
   immediately clear whether `None` means "set to null" or "not provided"
3. **No Wrapper Type**: Values are accessed directly, making it more difficult
   to distinguish the source of a `None` value

## Migrating to Maybe

We recommend migrating to [`Maybe`](./maybe.md) for new code. See the
[migration guide](./maybe.md#migrating-from-unset) for details.

### Quick Comparison

| Aspect          | UNSET                       | Maybe                            |
| --------------- | --------------------------- | -------------------------------- |
| Check absent    | `value is strawberry.UNSET` | `value is None`                  |
| Access value    | `value` (direct)            | `value.value` (via Some)         |
| Type annotation | `T \| None = UNSET`         | `Maybe[T]` or `Maybe[T \| None]` |
| Null handling   | Implicit                    | Explicit with `T \| None`        |

## Related

- [Maybe](./maybe.md) - The recommended alternative for input field handling
- [Input Types](./input-types.md) - Defining input types

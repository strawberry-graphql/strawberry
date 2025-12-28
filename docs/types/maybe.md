---
title: Maybe
---

# Maybe

In GraphQL, there's an important distinction between a field that is `null` and
a field that is completely absent from the input. Strawberry's `Maybe` type
allows you to differentiate between these states:

<Note>

`Maybe` is the recommended way to handle optional input fields in Strawberry. If
you're using `strawberry.UNSET` for this purpose, we encourage migrating to
`Maybe` for better type safety and clearer semantics. See
[Migrating from UNSET](#migrating-from-unset) for details.

</Note>

For `Maybe[str]`:

1. **Field present with a value**: `Some("hello")`
2. **Field completely absent**: `None`

For `Maybe[str | None]` (when you need to handle explicit nulls):

1. **Field present with a value**: `Some("hello")`
2. **Field present but explicitly null**: `Some(None)`
3. **Field completely absent**: `None`

This is particularly useful for update operations where you need to distinguish
between "set this field to null" and "don't change this field at all".

The design is inspired by Rust's
[`Option<T>`](https://doc.rust-lang.org/std/option/) type and similar patterns
in functional programming languages like Haskell's `Maybe` and Scala's `Option`.

## What problem does `strawberry.Maybe` solve?

Consider this common scenario: you have a user profile with an optional phone
number, and you want to provide an update mutation. With traditional nullable
types, you can't distinguish between:

- "Set the phone number to null" (remove the phone number)
- "Don't change the phone number" (leave it as is)

Both would be represented as `phone: null` in your GraphQL mutation.

## Basic Usage

Here's how to use `Maybe` in your Strawberry schema:

```python
import strawberry


@strawberry.input
class UpdateUserInput:
    name: str | None = None  # Traditional optional field
    phone: strawberry.Maybe[str | None]  # Maybe field


@strawberry.type
class User:
    name: str
    phone: str | None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user(self, user_id: str, input: UpdateUserInput) -> User:
        user = get_user(user_id)  # Your user retrieval logic

        # Traditional optional field - only update if provided
        if input.name is not None:
            user.name = input.name

        # Maybe field - check if field was provided at all
        if input.phone is not None:  # Field was provided
            user.phone = input.phone.value  # Access the actual value
        # If input.phone is None, the field wasn't provided - no change

        return user
```

## Understanding Some()

When a `Maybe` field has a value (including `null`), it's wrapped in a `Some()`
container:

```python
# Field provided with a string value
phone = strawberry.Some("555-1234")
print(phone.value)  # "555-1234"

# Field provided with null value
phone = strawberry.Some(None)
print(phone.value)  # None

# Field not provided at all
phone = None
print(phone)  # None
```

## GraphQL Schema

When you use `Maybe` in your schema, it appears as a nullable field in GraphQL:

```python
@strawberry.input
class UpdateUserInput:
    phone: strawberry.Maybe[str | None]
```

Generates this GraphQL schema:

```graphql
input UpdateUserInput {
  phone: String
}
```

## Common Patterns

### Input Types for Updates

`Maybe` is most commonly used in input types for update operations:

```python
@strawberry.input
class UpdatePostInput:
    title: strawberry.Maybe[str]  # Can be set to new value or omitted
    content: strawberry.Maybe[str]
    published: strawberry.Maybe[bool]
    tags: strawberry.Maybe[list[str] | None]  # Can be set, cleared, or omitted


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_post(self, post_id: str, input: UpdatePostInput) -> Post:
        post = get_post(post_id)

        # Only update fields that were explicitly provided
        if input.title:
            post.title = input.title.value
        if input.content:
            post.content = input.content.value
        if input.published:
            post.published = input.published.value
        if input.tags:
            post.tags = input.tags.value  # Could be None to clear tags

        return post
```

## Maybe vs Optional vs Nullable

Understanding the differences between these approaches:

| Type                            | Python     | GraphQL   | Absent   | Null          | Value          |
| ------------------------------- | ---------- | --------- | -------- | ------------- | -------------- |
| `str`                           | Required   | `String!` | ❌ Error | ❌ Error      | ✅ Value       |
| `str \| None`                   | Optional   | `String`  | ✅ None  | ✅ None       | ✅ Value       |
| `strawberry.Maybe[str]`         | Maybe      | `String`  | ✅ None  | ❌ Error      | ✅ Some(value) |
| `strawberry.Maybe[str \| None]` | Maybe+Null | `String`  | ✅ None  | ✅ Some(None) | ✅ Some(value) |

## Best Practices

### When to Use Maybe

Use `Maybe` when you need to distinguish between:

- Field not provided (no change)
- Field provided with null (clear/remove)
- Field provided with value (set/update)

Common use cases:

- Update mutations
- Patch operations
- Optional filters that need to distinguish between "not filtering" and
  "filtering by null"

### When to Use Optional Instead

Use regular optional types (`str | None`) when:

- You only need two states: value or null
- The field absence and null have the same meaning
- You're defining output types (GraphQL responses)

### Error Handling

Always check if a `Maybe` field was provided before accessing its value:

```python
# Good
if input.phone is not None:
    user.phone = input.phone.value

# Bad - will raise AttributeError if phone is None
user.phone = input.phone.value
```

### Helper Functions

You can create helper functions to make Maybe handling cleaner:

```python
def update_if_provided(obj, field_name: str, maybe_value):
    """Update object field only if Maybe value was provided."""
    if maybe_value is not None:
        setattr(obj, field_name, maybe_value.value)


# Usage
update_if_provided(user, "phone", input.phone)
update_if_provided(user, "email", input.email)
```

## Migrating from UNSET

If you're currently using `strawberry.UNSET` to differentiate between absent and
null values, we recommend migrating to `Maybe` for better type safety and
clearer semantics.

### Why Migrate?

`Maybe` provides advantages over `UNSET`:

1. **Type Safety**: `Maybe[T]` is a proper generic type that works correctly
   with type checkers, whereas `UNSET` is typed as `Any` which defeats static
   analysis
2. **Explicit Nullability**: With `UNSET`, you write `field: str | None = UNSET`
   where it's ambiguous whether `None` is a valid value or represents "absent".
   With `Maybe`, `Maybe[str]` means null is invalid, while `Maybe[str | None]`
   explicitly allows null as a value

### Migration Example

Before (using UNSET):

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
            user.name = input.name  # Could be a string or None
        if input.phone is not strawberry.UNSET:
            user.phone = input.phone
        return user
```

After (using Maybe):

```python
import strawberry


@strawberry.input
class UpdateUserInput:
    name: strawberry.Maybe[str | None]
    phone: strawberry.Maybe[str | None]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user(self, input: UpdateUserInput) -> User:
        if input.name is not None:
            user.name = input.name.value  # Access via .value
        if input.phone is not None:
            user.phone = input.phone.value
        return user
```

### Key Differences

| Aspect          | UNSET                       | Maybe                            |
| --------------- | --------------------------- | -------------------------------- |
| Check absent    | `value is strawberry.UNSET` | `value is None`                  |
| Access value    | `value` (direct)            | `value.value` (via Some)         |
| Type annotation | `T \| None = UNSET`         | `Maybe[T]` or `Maybe[T \| None]` |
| Null handling   | Implicit                    | Explicit with `T \| None`        |

### Codemod

If you have existing `Maybe[T]` annotations that need to accept explicit null
values, Strawberry provides a codemod to convert them to `Maybe[T | None]`:

```bash
python -m libcst.tool codemod strawberry.codemods.maybe_optional.ConvertMaybeToOptional .
```

Note: This codemod is for updating `Maybe` annotations, not for migrating from
`UNSET` to `Maybe`. Migration from `UNSET` requires manual changes to update
both the type annotations and the value access patterns (from `value` to
`value.value`).

## Related Types

- [Input Types](./input-types.md) - Using Maybe in input type definitions
- [Resolvers](./resolvers.md) - Using Maybe in resolver arguments
- [Union Types](./union.md) - Combining Maybe with union types
- [Scalars](./scalars.md) - Custom scalar types with Maybe

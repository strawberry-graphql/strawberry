---
title: Operation directives
---

# Operation directives

GraphQL uses directives to modify the evaluation of an item in the schema or the
operation. Operation directives can be included inside any operation (query,
subscription, mutation) and can be used to modify the execution of the operation
or the values returned by the operation.

Directives can help avoid having to create resolvers for values that can be
computed via the values of additional fields.

All Directives are proceeded by `@` symbol

# Default Operation directives

Strawberry provides two default operation directives:

- `@skip(if: Boolean!)` - if Boolean is true, the given item is NOT resolved by
  the GraphQL Server

- `@include(if: Boolean!)` - if Boolean is false, the given item is NOT resolved
  by the GraphQL Server

<Note>

`@deprecated(reason: String)` IS NOT compatible with Operation directives.
`@deprecated` is exclusive to [Schema Directives](./schema-directives.md)

</Note>

**Examples of Default Operation directives**

```graphql
# @include
query getPerson($includePoints: Boolean!) {
  person {
    name
    points @include(if: $includePoints)
  }
}

# @skip
query getPerson($hideName: Boolean!) {
  person {
    name @skip(if: $hideName)
    points
  }
}
```

# Custom Operation directives

Custom directives must be defined in the schema to be used within the query and
can be used to decorate other parts of the schema.

```python
# Definition
@strawberry.directive(
    locations=[DirectiveLocation.FIELD], description="Make string uppercase"
)
def turn_uppercase(value: str):
    return value.upper()


@strawberry.directive(locations=[DirectiveLocation.FIELD])
def replace(value: str, old: str, new: str):
    return value.replace(old, new)
```

```graphql
# Use
query People($identified: Boolean!) {
  person {
    name @turnUppercase
  }
  jess: person {
    name @replace(old: "Jess", new: "Jessica")
  }
  johnDoe: person {
    name @replace(old: "Jess", new: "John") @include(if: $identified)
  }
}
```

# Locations for Operation directives

Directives can only appear in _specific_ locations inside the query. These
locations must be included in the directive's definition. In Strawberry the
location is defined in the directive function's parameter `locations`.

```graphql
@strawberry.directive(locations=[DirectiveLocation.FIELD])
```

**Operation directives possible locations**

Operation directives can be applied to many different parts of an operation.
Here's the list of all the allowed locations:

- `QUERY`
- `MUTATION`
- `SUBSCRIPTION`
- `FIELD`
- `FRAGMENT_DEFINITION`
- `FRAGMENT_SPREAD`
- `INLINE_FRAGMENT`

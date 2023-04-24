---
title: Operational Directives
---

# Operational Directives

GraphQL uses directives to modify the evaluation of an item in the schema or the operation.
Operational Directives are included inside query and supports custom and compatible default directives. Directives can help avoid having to create resolvers for values that can be computed via the values
of additional fields.

All Directives are proceeded by `@` symbol

# Default Operational Directives

`@skip(if: Boolean!)` - if Boolean is true, the given item is NOT resolved by the GraphQL Server

`@include(if: Boolean!)` - if Boolean is false, the given item is NOT resolved by the GraphQL Server

<Note>

`@deprecated(reason: String)` IS NOT compatible with Operational Directives. `@deprecated` is exclusive
to Schema Directives(Include Link)

</Note>

**Examples of Default Operational Directives**

```graphql
#@include
query getPerson($includePoints: Boolean!) {
  person {
    name
    points @include(if: $includePoints)
  }
}

#@skip
query getPerson($hideName: Boolean!) {
  person {
    name @skip(if: $hideName)
    points
  }
}
```

# Custom Operational Directives

Custom directives must be defined in the schema to be used within the query and can be used to decorate
other parts of the schema.

```graphql
# Definition
@strawberry.directive(locations=[DirectiveLocation.FIELD], description="Make string uppercase")
    def turn_uppercase(value: str):
        return value.upper()

@strawberry.directive(locations=[DirectiveLocation.FIELD])
    def replace(value: str, old: str, new: str):
        return value.replace(old, new)

# Use
query People($identified: Boolean!){
        person {
            name @turnUppercase
        }
        jess: person {
            name @replace(old: "Jess", new: "Jessica")
        }
        johnDoe: person {
            name @replace(old: "Jess", new: "John") @include(if: $identified)
}
```

# Locations for Operational Directives

Directives can only appear in _specific_ locations inside the query. These locations must be included in the
directive's definition. In Strawberry the location is defined in the directive function's parameter `locations`.

```graphql
@strawberry.directive(locations=[DirectiveLocation.FIELD])
```

**Operational Directives possible locations**

- QUERY
- MUTATION
- SUBSCRIPTION
- FIELD
- FRAGMENT_DEFINITION
- FRAGMENT_SPREAD
- INLINE_FRAGMENT

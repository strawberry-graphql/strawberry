---
title: Private Fields
---

# Private Fields

Private (external) fields can provide local context for later resolution. These
fields will act as plain fields so will not be exposed in the GraphQL API.

Some uses include:

- Context that relies upon field inputs.
- Avoiding fully materializing an object hierarchy (lazy resolution)

# Defining a private field

Specifying a field with `strawberry.Private[...]` will desigate it as internal
and not for GraphQL.

# Example

Consider the following type, which can accept any Python object and handle
converting it to string, representation, or templated output:

```python
@strawberry.type
class Stringable:
    value: strawberry.Private[object]

    @strawberry.field
    def string(self) -> str:
        return str(self.value)

    @strawberry.field
    def repr(self) -> str:
        return repr(self.value)

    @strawberry.field
    def format(self, template: str) -> str:
        return template.format(my=self.value)
```

The `Private[...]` type lets Strawberry know that this field is not a GraphQL
field. "value" is a regular field on the class, but it is not exposed on the
GraphQL API.

```python
@strawberry.type
class Query:
    @strawberry.field
    def now(self) -> Stringable:
        return Stringable(value=datetime.datetime.now())
```

Queries can then select the fields and formats desired, but formatting only
happens as requested:

<CodeGrid>

```graphql
{
  now {
    format(template: "{my.year}")
    string
    repr
  }
}
```

```json
{
  "data": {
    "now": {
      "format": "2022",
      "string": "2022-09-03 17:03:04.923068",
      "repr": "datetime.datetime(2022, 9, 3, 17, 3, 4, 923068)"
    }
  }
}
```

</CodeGrid>

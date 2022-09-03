---
title: Private Fields
---

# Private Fields

Private (external) fields can provide local context for later resolution.
These fields will act as plain dataclass fields and not become attached to
strawberry resolvers.

Some uses include:

- Context that relies upon field inputs.
- Avoiding fully materializing an object hierarchy (lazy resolution)

# Defining a private field

Specifying a field with `strawberry.Private[...]` will desigate the field
as for dataclasses, and not a graphql field.

# Example

Consider the following type, which can accept any Python object and handle
converting it to string, representation, or templated output:

```

@strawberry.type
class Stringable:
    value: strawberry.Private[object]

    @strawberry.field
    def string(self) -> str:
        return str(self.object)

    @strawberry.field
    def repr(self) -> str:
        return repr(self.object)

    @strawberry.field
    def format(self, template: str) -> str:
        return template.format(my=self.object)

```

The `Private[...]` type lets Strawberry know that this field is not a GraphQL field. "value" is a regular field on the class, but it is not exposed on the GraphQL API.

```

@strawberry.type
class Query:
    @strawberry.field
    def now(self) -> Stringable:
        return Stringable(object=datetime.datetime.now())

```

Queries can then select the fields and formats desired, but formatting only
happens as requested:

```graphql+json
{
  now {
    format(template: "{my.year}")
    string
    repr
  }
}

---

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

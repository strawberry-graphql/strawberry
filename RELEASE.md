---
release type: minor
---

This release adds an error for input types with fields that have resolvers,
raised when the input type is created:

```python
import strawberry


@strawberry.input
class UserInput:
    name: str

    @strawberry.field
    def upper_name(self) -> str:
        return self.name.upper()
```

Input types only hold the values sent by the client, so the resolver never ran:
the schema published `upperName: String!` as an input field, so requests that
left it out failed, and requests that sent it failed with
`UserInput.__init__() got an unexpected keyword argument 'upper_name'`. The same
happened to input types inheriting from an output type with resolvers.

Strawberry now raises a `ResolverFieldOnInputError` pointing at the resolver
instead. Remove the resolver, or move the field to an output type.

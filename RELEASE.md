---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes a bug with nullable input fields.
    🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes a bug with nullable input fields.
    These fields are now correctly treated as optional.
---

This release fixes a bug with nullable input fields.

Given a Strawberry schema like
```python
@strawberry.input
class RunInput:
    required: int
    optional: str | None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def run(self, input: RunInput) -> int: ...
```

and the following GraphQL query
```graphql
mutation {
    run(input: {required: 42})
}
```

Previous versions of Strawberry raised a `TypeError: RunInput.__init__() missing 1 required keyword-only argument: 'optional'`.
This meant that clients had to  explicitly specify nullable fields as `null`:
```graphql
mutation {
    run(input: {required: 42, optional: null})
}
```

However, according to the [GraphQL spec](https://spec.graphql.org/draft/#sec-Non-Null.Nullable-vs-Optional),
nullable input fields are always optional:

> Nullable types are always optional and non-null types are always required.

This release fixes the `TypeError` and now correctly treats nullable input fields as optional.

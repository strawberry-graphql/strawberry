---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! OneOf input types with a required field or
    a field with a default now raise a clear error when the schema is built,
    instead of failing on every request.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. OneOf input types with a required field or
    a field with a default value now raise a clear error when the schema is
    built. GraphQL doesn't allow these fields, and the input either failed on
    every request or only worked with one of its fields.
---

This release adds a check for the fields of OneOf input types, when the schema
is built. GraphQL requires them to be nullable and without a default value, as
clients set exactly one of them, but Strawberry didn't check it:

```python
import strawberry


@strawberry.input(one_of=True)
class SearchBy:
    name: str | None = None
    email: str | None = None
```

The schema printed `name: String = null` and `email: String = null`, so GraphQL
filled in the other field and every request failed with
`OneOf Input Object 'SearchBy' must specify exactly one key.` A required field,
like `name: str`, made the input only work with that field. The printed schema
was also invalid for other GraphQL tools.

Strawberry now raises an `InvalidOneOfInputFieldError` when the schema is built
instead. Declare the fields as nullable and without a default, and Strawberry
sets the ones that the client didn't set to `None`:

```python
@strawberry.input(one_of=True)
class SearchBy:
    name: str | None
    email: str | None
```

Default values of OneOf input types now leave out the fields set to `None`, so
`by: SearchBy = SearchBy(name="Patrick", email=None)` prints as
`{ name: "Patrick" }` instead of `{ name: "Patrick", email: null }`, which isn't
a valid OneOf value.

The OneOf docs now use this style instead of `strawberry.Maybe`, which still
works: OneOf fields can't be set to `null`, so `Maybe` doesn't add anything
there.

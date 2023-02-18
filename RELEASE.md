Release type: patch

This release adds the `OneOf` directive to indicate that the input type is a `oneOf` Input Object, where exactly one of the input fields must be provided as input,
or otherwise the server returns a validation error.


Instead of defining a field for each property which a user can be retrieved we can now have a single field `user` that accepts all properties via a `UserByInput` `OneOf` input object, knowing that only one of the properties (either the ID or the email) can be provided:


```python
import strawberry
from strawberry.schema_directives import OneOf


@strawberry.input(directives=[OneOf])
class UserByInput:
    id: strawberry.ID
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self, by: UserByInput) -> User:
        ...
```

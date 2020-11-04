Release type: bugfix

Allow interfaces to implement other interfaces.
This may be useful if you are using the relay pattern
or if you want to model base interfaces that can be extended.

Example:
```python
import strawberry


@strawberry.interface
class Error:
    message: str

@strawberry.interface
class FieldError(Error):
    message: str
    field: str

@strawberry.type
class PasswordTooShort(FieldError):
    message: str
    field: str
    fix: str
```
Produces the following SDL:
```graphql
interface Error {
  message: String!
}

interface FieldError implements Error {
  message: String!
  field: String!
}

type PasswordTooShort implements FieldError & Error {
  message: String!
  field: String!
  fix: String!
}
```

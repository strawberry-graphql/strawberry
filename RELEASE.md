---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! This release adds exception handlers, a building block for integrations that want to turn expected Python errors into typed GraphQL results. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds exception handlers, a schema-level hook for integrations that need to turn framework validation errors, such as Pydantic errors, into typed GraphQL union results. Most applications will not need to use this directly, but it gives framework integrations a cleaner path without adding try/except blocks to every resolver.
---

This release adds configurable exception handlers that map Python exceptions to
typed GraphQL union results.

Most applications do not need to adopt this directly. It is primarily useful for
integrations and framework-level helpers: for example, catching validation
exceptions from a library such as Pydantic and exposing them as an explicit
GraphQL error type, without requiring every resolver to catch and convert those
exceptions manually.

Handlers are passed to `strawberry.Schema` (and `strawberry.federation.Schema`):

```python
import strawberry
from strawberry.types.field import StrawberryField


class ValidationProblem(Exception):
    pass


@strawberry.type
class ValidationError:
    message: str


class ValidationErrorHandler(
    strawberry.ExceptionHandler[ValidationProblem, ValidationError]
):
    def handle(
        self,
        exception: ValidationProblem,
        *,
        field: StrawberryField,
        info: strawberry.Info,
    ) -> ValidationError:
        return ValidationError(message=str(exception))


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    exception_handlers=[ValidationErrorHandler()],
)
```

Handlers can alternatively declare `exception_type` and `error_type` class
attributes instead of type parameters, which also covers types that are only
known at runtime. Declaring both a type parameter and a conflicting attribute
for the same slot raises an error at schema creation.

Strawberry only converts the exception when the field return type includes the
handler's GraphQL error type. Other fields continue to raise normal GraphQL
errors, so applications can opt in one field at a time. Exceptions raised by
the resolver, during argument conversion, or by field extensions are all
covered.

Exception handlers apply to query and mutation fields. Subscriptions are not
covered: exceptions raised while establishing a subscription are not converted
into union results.

---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! This release adds a
    `mask_pre_execution_errors` option to `MaskErrors`, so clients can still see
    why their query is invalid. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds a
    `mask_pre_execution_errors` option to the `MaskErrors` extension, so syntax
    and validation errors can reach clients while the errors your resolvers
    raise stay masked. It also fixes an error leak when one `MaskErrors`
    instance serves concurrent operations.
---

This release adds a `mask_pre_execution_errors` option to the `MaskErrors` extension.

`MaskErrors` masks every error. This includes the syntax errors of a document and the validation errors against the schema, so a client that sends an invalid query gets only the generic message. Set the new option to `False` to send these errors to the client. The errors that your resolvers raise stay masked:

```python
import strawberry
from strawberry.extensions import MaskErrors


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"

    @strawberry.field
    def hidden_error(self) -> str:
        raise KeyError("This error will not be visible")


schema = strawberry.Schema(
    Query,
    extensions=[
        lambda: MaskErrors(mask_pre_execution_errors=False),
    ],
)

# "Cannot query field 'helloo' on type 'Query'. Did you mean 'hello'?"
schema.execute_sync("{ helloo }")

# "Unexpected error."
schema.execute_sync("{ hiddenError }")
```

The default value is `True`, which keeps the current behaviour. Validation errors give the names of the fields, the arguments and the types of your schema. Thus disable the option only if the clients can know the shape of the schema.

This release also fixes an error leak in `MaskErrors`. The extension kept some of its state on the instance. When one instance served more than one operation at the same time – which the deprecated `extensions=[MaskErrors()]` form does – a frame of an open stream could stop the extension from masking the errors of another operation, and the message of the original exception reached the client. `MaskErrors` now keeps this state per operation.

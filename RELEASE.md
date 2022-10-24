Release type: minor

This release adds a new optional parameter `status_code_hook` to the `MaskErrors` extension that can be used to dynamically set the Response `status_code` based on the errors raised.

```python
import strawberry
from strawberry.extensions import MaskErrors
from graphql.error import GraphQLError
from strawberry.types import ExecutionContext

class VisibleError(Exception):
    pass

def status_code_hook(error: GraphQLError, execution_context: ExecutionContext) -> None:
    response = execution_context.context['response']
    existing_status_code = response.status_code
    if error.original_error and isinstance(error.orginal_error, VisibleError):
        new_status_code = 400
    else:
        new_status_code = 500
    if new_status_code > existing_status_code:
        response.status_code = new_status_code

schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(status_code_hook=status_code_hook),
    ]
)
```

Release type: patch

This release fixes that the `create_type` tool asked users to pass a `name` for
fields without resolvers even when a `name` was already provided.

The following code now works as expected:

```python
import strawberry
from strawberry.tools import create_type

first_name = strawberry.field(name="firstName")
Query = create_type(f"Query", [first_name])
```

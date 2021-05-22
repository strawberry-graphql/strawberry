Release type: patch

Add `root_value` to `ExecutionContext` type so that it can be accessed in
extensions.

Example:

```python
import strawberry
from strawberry.extensions import Extension

class MyExtension(Extension):
    def on_request_end(self):
        root_value = self.execution_context.root_value
        # do something with the root_value
```

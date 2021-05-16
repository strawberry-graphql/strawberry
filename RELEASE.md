Release type: minor

This release adds extra values to the ExecutionContext object so that it can be
used by extensions and the `Schema.process_errors` function.

The full ExecutionContext object now looks like this:

```python
from graphql import ExecutionResult as GraphQLExecutionResult
from graphql.error.graphql_error import GraphQLError
from graphql.language import DocumentNode as GraphQLDocumentNode

@dataclasses.dataclass
class ExecutionContext:
    query: str
    context: Any = None
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = None

    graphql_document: Optional[GraphQLDocumentNode] = None
    errors: Optional[List[GraphQLError]] = None
    result: Optional[GraphQLExecutionResult] = None
```

and can be accessed in any of the extension hooks:

```python
from strawberry.extensions import Extension

class MyExtension(Extension):
    def on_request_end(self):
        result = self.execution_context.result
        # Do something with the result

schema = strawberry.Schema(query=Query, extensions=[MyExtension])
```

---

Note: This release also removes the creation of an ExecutionContext object in the web
framework views. If you were relying on overriding the `get_execution_context`
function then you should change it to `get_request_data` and use the 
`strawberry.http.parse_request_data` function to extract the pieces of data
needed from the incoming request.

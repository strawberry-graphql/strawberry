Release type: minor

Update execution to allow adding instances of `Exception` type to `info.context.partial_errors` to get added to the result after execution, allowing users to add errors to the errors array from a field resolver while still resolving that field.

**Usage examples:**

Basic usage:

```python
import strawberry


@strawberry.field
def query(self, info) -> bool:
    info.context.partial_errors.append(Exception("Partial failure"))
    return True
```

Results:

```json
{
  "data": {
    "query": true
  },
  "errors": [
    {
      "message": "Partial failure"
    }
  ]
}
```

Located usage:

```python
import strawberry

from graphql import located_error


@strawberry.field
def query(self, info) -> bool:
    nodes = [next(n for n in info.field_nodes if n.name.value == "query")]
    info.context.partial_errors.append(
        located_error(
            Exception("Error with location and path information"),
            nodes=nodes,
            path=info.path.as_list(),
        ),
    )
    return True
```

Results:

```json
{
  "data": {
    "query": true
  },
  "errors": [
    {
      "message": "Error with location and path information",
      "location": {
        "line": 1,
        "column": 9
      },
      "path": ["query"]
    }
  ]
}
```

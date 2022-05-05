---
title: Custom extensions
---

# Custom extensions

Strawberry provides support for adding extensions. Extensions can be used to
hook into different parts of the GraphQL execution and to provide additional
results to the GraphQL response.

To create a custom extensions you can use extend from our `Extension` base
class:

```python
import strawberry
from strawberry.extensions import Extension

class MyExtension(Extension):
    def get_results(self):
        return {
            "example": "this is an example for an extension"
        }

schema = strawberry.Schema(query=Query, extensions=[MyExtension])
```

## Hooks

### Request

`on_request_start` and `on_request_end` can be used to run code when a GraphQL request
starts and ends. Both methods can alternatively be implemented asynchronously.

```python
from strawberry.extensions import Extension

class MyExtension(Extension):
    def on_request_start(self):
        print('GraphQL request start')

    def on_request_end(self):
        print('GraphQL request end')
```

### Resolve

`resolve` can be used to run code before or after the execution of resolvers, this
method _must_ call `_next` with all the arguments, as they will be needed by the
resolvers.

Note that `resolve` can also be implemented asynchronously.

```python
from strawberry.types import Info
from strawberry.extensions import Extension

class MyExtension(Extension):
    def resolve(self, _next, root, info: Info, *args, **kwargs):
        return _next(root, info, *args, **kwargs)
```

### Get results

`get_results` allows to return a dictionary of data or alternatively an awaitable
resolving to a dictionary of data that will be included in the GraphQL response.

```python
from typing import Any, Dict
from strawberry.extensions import Extension

class MyExtension(Extension):
    def get_results(self) -> Dict[str, Any]:
        return {}
```

### Validation

`on_validation_start` and `on_validation_end` can be used to run code on the validation
step of the GraphQL execution. Both methods can be implemented asynchronously.

```python
from strawberry.extensions import Extension

class MyExtension(Extension):
    def on_validation_start(self):
        print('GraphQL validation start')

    def on_validation_end(self):
        print('GraphQL validation end')
```

### Parsing

`on_parsing_start` and `on_parsing_end` can be used to run code on the parsing step of
the GraphQL execution. Both methods can be implemented asynchronously.

```python
from strawberry.extensions import Extension

class MyExtension(Extension):
    def on_parsing_start(self):
        print('GraphQL parsing start')

    def on_parsing_end(self):
        print('GraphQL parsing end')
```

### Execution

`on_executing_start` and `on_executing_end` can be used to run code on the execution step of
the GraphQL execution. Both methods can be implemented asynchronously.

```python
from strawberry.extensions import Extension

class MyExtension(Extension):
    def on_executing_start(self):
        print('GraphQL execution start')

    def on_executing_end(self):
        print('GraphQL execution end')
```

#### Examples:

<details>
  <summary>In memory cached execution</summary>

```python
import json
import strawberry
from strawberry.extensions import Extension

# Use an actual cache in production so that this doesn't grow unbounded
response_cache = {}

class ExecutionCache(Extension):
    def on_executing_start(self):
        # Check if we've come across this query before
        execution_context = self.execution_context
        self.cache_key = (
            f"{execution_context.query}:{json.dumps(execution_context.variables)}"
        )
        if self.cache_key in response_cache:
            self.execution_context.result = response_cache[self.cache_key]

    def on_executing_end(self):
        execution_context = self.execution_context
        if self.cache_key not in response_cache:
            response_cache[self.cache_key] = execution_context.result


schema = strawberry.Schema(
    Query,
    extensions=[
        ExecutionCache,
    ]
)
```

</details>

<details>
  <summary>Rejecting a request before executing it</summary>

```python
import strawberry
from strawberry.extensions import Extension

class RejectSomeQueries(Extension):
    def on_executing_start(self):
        # Reject all operations called "RejectMe"
        execution_context = self.execution_context
        if execution_context.operation_name == "RejectMe":
            self.execution_context.result = GraphQLExecutionResult(
                data=None,
                errors=[GraphQLError("Well you asked for it")],
            )


schema = strawberry.Schema(
    Query,
    extensions=[
        RejectSomeQueries,
    ]
)
```

</details>

### Execution Context

The `Extension` object has an `execution_context` property on `self` of type
`ExecutionContext`.

This object can be used to gain access to additional GraphQL context, or the request
context. Take a look at the [`ExecutionContext` type](https://github.com/strawberry-graphql/strawberry/blob/main/strawberry/types/execution.py)
for available data.

```python
from strawberry.extensions import Extension

from mydb import get_db_session

class MyExtension(Extension):
    def on_request_start(self):
        self.execution_context.context["db"] = get_db_session()

    def on_request_end(self):
        self.execution_context.context["db"].close()
```

---
title: Custom extensions
---

# Custom extensions

Strawberry provides support for adding extensions. Extensions can be used to
hook into different parts of the GraphQL execution and to provide additional
results to the GraphQL response.

To create a custom extensions you can use extend from our `SchemaExtension` base
class:

```python
import strawberry
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def get_results(self):
        return {"example": "this is an example for an extension"}


schema = strawberry.Schema(query=Query, extensions=[MyExtension])
```

## Hooks

### Resolve

`resolve` can be used to run code before and after the execution of **all**
resolvers. When calling the underlying resolver using `_next`, all of the
arguments to resolve need to be passed to `_next`, as they will be needed by the
resolvers.

If you need to wrap only certain field resolvers with additional logic, please
check out [field extensions](field-extensions.md).

Note that `resolve` can also be implemented asynchronously.

```python
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def resolve(self, _next, root, info: strawberry.Info, *args, **kwargs):
        return _next(root, info, *args, **kwargs)
```

### Get results

`get_results` allows to return a dictionary of data or alternatively an
awaitable resolving to a dictionary of data that will be included in the GraphQL
response.

```python
from typing import Any, Dict
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def get_results(self) -> Dict[str, Any]:
        return {}
```

### Lifecycle hooks

Lifecycle hooks runs before graphql operation occur and after it is done.
Lifecycle hooks uses generator syntax. In example: `on_operation` hook can be
used to run code when a GraphQL operation starts and ends.

```python
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def on_operation(self):
        print("GraphQL operation start")
        yield
        print("GraphQL operation end")
```

<details>
  <summary>Extend error response format</summary>

```python
class ExtendErrorFormat(SchemaExtension):
    def on_operation(self):
        yield
        result = self.execution_context.result
        if getattr(result, "errors", None):
            result.errors = [
                StrawberryGraphQLError(
                    extensions={"additional_key": "additional_value"},
                    nodes=error.nodes,
                    source=error.source,
                    positions=error.positions,
                    path=error.path,
                    original_error=error.original_error,
                    message=error.message,
                )
                for error in result.errors
            ]


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        raise Exception("This error occurred while querying the ping field")


schema = strawberry.Schema(query=Query, extensions=[ExtendErrorFormat])
```

</details>

#### Supported lifecycle hooks:

- Validation

`on_validate` can be used to run code on the validation step of the GraphQL
execution.

```python
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def on_validate(self):
        print("GraphQL validation start")
        yield
        print("GraphQL validation end")
```

- Parse

`on_parse` can be used to run code on the parsing step of the GraphQL execution.

```python
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def on_parse(self):
        print("GraphQL parsing start")
        yield
        print("GraphQL parsing end")
```

- Execution

`on_execute` can be used to run code on the execution step of the GraphQL
execution.

```python
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def on_execute(self):
        print("GraphQL execution start")
        yield
        print("GraphQL execution end")
```

#### Examples:

<details>
  <summary>In memory cached execution</summary>

```python
import json
import strawberry
from strawberry.extensions import SchemaExtension

# Use an actual cache in production so that this doesn't grow unbounded
response_cache = {}


class ExecutionCache(SchemaExtension):
    def on_execute(self):
        # Check if we've come across this query before
        execution_context = self.execution_context
        self.cache_key = (
            f"{execution_context.query}:{json.dumps(execution_context.variables)}"
        )
        if self.cache_key in response_cache:
            self.execution_context.result = response_cache[self.cache_key]
        yield
        execution_context = self.execution_context
        if self.cache_key not in response_cache:
            response_cache[self.cache_key] = execution_context.result


schema = strawberry.Schema(
    Query,
    extensions=[
        ExecutionCache,
    ],
)
```

</details>

<details>
  <summary>Rejecting an operation before executing it</summary>

```python
import strawberry
from strawberry.extensions import SchemaExtension


class RejectSomeQueries(SchemaExtension):
    def on_execute(self):
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
    ],
)
```

</details>

### Execution Context

The `SchemaExtension` object has an `execution_context` property on `self` of
type `ExecutionContext`.

This object can be used to gain access to additional GraphQL context, or the
request context. Take a look at the
[`ExecutionContext` type](https://github.com/strawberry-graphql/strawberry/blob/main/strawberry/types/execution.py)
for available data.

```python
from strawberry.extensions import SchemaExtension

from mydb import get_db_session


class MyExtension(SchemaExtension):
    def on_operation(self):
        self.execution_context.context["db"] = get_db_session()
        yield
        self.execution_context.context["db"].close()
```

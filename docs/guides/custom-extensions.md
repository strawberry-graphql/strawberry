---
title: Schema extensions
---

# Schema extensions

Strawberry provides support for adding extensions to your schema. Schema
extensions can be used to hook into different parts of the GraphQL execution and
to provide additional results to the GraphQL response.

To create a custom extension you can extend from our `SchemaExtension` base
class:

```python
import strawberry
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def get_results(self):
        return {"example": "this is an example for an extension"}


schema = strawberry.Schema(query=Query, extensions=[MyExtension])
```

## Passing extensions

Extensions can be passed to the schema as either:

- a **class** (no constructor arguments):

  ```python
  import strawberry
  from strawberry.extensions import MyExtension

  schema = strawberry.Schema(query=Query, extensions=[MyExtension])
  ```

- a **factory** (configured constructor):

  ```python
  import strawberry
  from strawberry.extensions import MaxTokensLimiter

  schema = strawberry.Schema(
      query=Query,
      extensions=[lambda: MaxTokensLimiter(max_token_count=100)],
  )
  ```

In both cases Strawberry calls the class or the factory once per request and
uses the returned extension. With the recommended forms above you get a fresh
extension per request, so any mutable state you keep on `self` is automatically
isolated across concurrent requests. If your factory returns a long-lived shared
instance instead of a new one each call, request-scoped state on `self`
(including `execution_context`) will leak across concurrent requests. Keep
cross-request state in module-level or class-level storage instead.

> Passing an extension instance directly (`extensions=[MyExtension()]`) is
> deprecated and is no longer accepted by the type signature, so type checkers
> (mypy, pyright) will report it. Strawberry still uses the instance at runtime
> for backwards compatibility and emits a `DeprecationWarning`, but the same
> instance is reused for every request, so concurrent requests can observe each
> other's `ExecutionContext`. Migrate to passing the class or a factory callable
> to silence the warning and get per-request isolation.

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
import strawberry
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def resolve(self, _next, root, info: strawberry.Info, *args, **kwargs):
        return _next(root, info, *args, **kwargs)
```

Annotating `info` with `strawberry.Info` opts the extension into Strawberry's
Info API, including a custom `info_class` configured on the schema. Access the
underlying graphql-core object with `info._raw_info` when integrating with an
API that requires `GraphQLResolveInfo`.

For graphql-core-only fields such as introspection fields, `python_name` falls
back to the GraphQL field name and `get_argument_definition` returns `None`.
Because those fields have no Strawberry return type, `return_type` raises a
`ValueError`; use `info._raw_info.return_type` when handling them.

#### Migrating from `GraphQLResolveInfo`

An unannotated `info` parameter, or one annotated as `GraphQLResolveInfo`, keeps
the previous runtime behavior for compatibility but emits a
`DeprecationWarning`. This compatibility behavior will be removed in Strawberry
1.0.

The upgrade command opts direct `SchemaExtension` subclasses into
`strawberry.Info` while preserving their existing use of the raw object:

```shell
strawberry upgrade schema-extension-info .
```

For example, the codemod renames the new parameter and retains `info` as an
alias for the graphql-core object. This makes the automated change
behavior-preserving and leaves semantic cleanup to a follow-up review:

```python
class MyExtension(SchemaExtension):
    def resolve(self, _next, root, strawberry_info: strawberry.Info, **kwargs):
        info = strawberry_info._raw_info
        return _next(root, info, **kwargs)
```

Indirect subclasses must be reviewed manually; unrecognized annotations on
direct subclasses are reported by the codemod. The following prompt can be given
to a coding agent after running the codemod:

```text
Find all SchemaExtension subclasses that override resolve. Ensure the Info
parameter is annotated as strawberry.Info and preserve every _next call.

Replace access through info._raw_info with Strawberry Info properties when they
are equivalent: field_name, context, root_value, variable_values, operation,
and path. Review schema and return_type carefully because Strawberry and
graphql-core expose different objects for those properties. Keep _raw_info for
parent_type, field_nodes, fragments, is_awaitable, graphql-core helpers, and
APIs that explicitly require GraphQLResolveInfo.

Do not modify FieldExtension classes. Run the affected sync and async extension
tests, including custom info_class, mixed legacy/new extension chains, and
introspection queries.
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

- Stream result

`on_stream_result` wraps each result yielded by `Schema.stream`, including
subscription events, queries or mutations executed over WebSockets, SSE, or
multipart responses. On transports that support experimental incremental
execution, it also wraps the delivery frames produced by `@defer` or `@stream`.
It can inspect or mutate a result before the transport sends it and run cleanup
after the transport consumes it.

`Schema.subscribe` uses the same streaming path, so this hook runs for every
subscription event. With experimental incremental execution enabled, it also
runs for every `@defer` or `@stream` response frame: an initial result followed
by subsequent patches.

```python
from collections.abc import Iterator

from strawberry.extensions import SchemaExtension
from strawberry.types import StreamExecutionResult


class MyExtension(SchemaExtension):
    def on_stream_result(self, result: StreamExecutionResult) -> Iterator[None]:
        print("GraphQL stream result ready", result)
        yield
        print("GraphQL stream result consumed", result)
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

<details>
  <summary>Operation Extensions (Requires GraphQL 3.3)</summary>

```python
import time
import strawberry
from strawberry.extensions import SchemaExtension


class QueryStatsExtension(SchemaExtension):
    def on_operation(self):
        execution_context = self.execution_context

        if execution_context.operation_extensions:
            if execution_context.operation_extensions.get("stats", False):
                start_time = time.time()
                yield
                end_time = time.time()
                self.execution_context.extensions_results["stats"] = {
                    "query_time": end_time - start_time
                }
                return

        yield


schema = strawberry.Schema(
    Query,
    extensions=[
        QueryStatsExtension,
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

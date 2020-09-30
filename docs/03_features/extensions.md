---
title: Extensions
path: /docs/feature/extensions
---

# Extensions

Strawberry provides support for adding extensions. Extensions can be used to
hook into different parts of the GraphQL execution and to provide additional
results to the GraphQL response.

To enable extensions you can pass them when creating a schema, here's an example
that enables the Apollo tracing extension:

```python
from strawberry.extensions.tracing import ApolloTracingExtension

schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension()])
```

## Creating custom extensions

To create a custom extensions you can use extend from our `Extension` base
class:

```python
from strawberry.extensions import Extension

class MyExtension(Extension):
    def get_results(self):
        return {
            "example": "this is an example for an extension"
        }
```

You can use the following hooks to run code when needed:

- `on_request_start`

```python
class Extension:  # pragma: no cover
    def on_request_start(self, *, execution_context: ExecutionContext):
        ...

    def on_request_end(self, *, execution_context: ExecutionContext):
        ...

    def on_validation_start(self):
        ...

    def on_validation_end(self):
        ...

    def on_parsing_start(self):
        ...

    def on_parsing_end(self):
        ...

    def resolve(self, _next, root, info, *args, **kwargs):
        ...

    def get_results(self):
        return {}
```

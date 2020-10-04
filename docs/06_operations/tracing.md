---
title: Tracing
path: /docs/ops/tracing
---

# Tracing

We currently provide support for the Apollo tracing protocol, to enable it you
can use the ApolloTracingExtension provided:

```python
from strawberry.extensions.tracing import ApolloTracingExtension

schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension])
```

Note that if you're not running under ASGI you'd need to use the sync version of
ApolloTracingExtension:

```python
from strawberry.extensions.tracing import ApolloTracingExtensionSync

schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtensionSync])
```

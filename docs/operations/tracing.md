---
title: Tracing
---

# Tracing

## Apollo

To enable [Apollo tracing](https://github.com/apollographql/apollo-tracing) you
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

## Open Telemetry

In addition to Apollo Tracing we also support
[opentelemetry](https://opentelemetry.io/), using the OpenTelemetryExtension.

You also need to install the extras for opentelemetry by doing:

```
pip install strawberry-graphql[opentelemetry]
```

```python
from strawberry.extensions.tracing import OpenTelemetryExtension

schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])
```

Note that if you're not running under ASGI you'd need to use the sync version of
OpenTelemetryExtension:

```python
from strawberry.extensions.tracing import OpenTelemetryExtensionSync

schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtensionSync])
```

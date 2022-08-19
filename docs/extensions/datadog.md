---
title: DatadogExtension
summary: Add Datadog tracing to your GraphQL server.
tags: tracing
---

# `DatadogExtension`

This extension adds support for tracing with Datadog.

<Note>

Make sure you have `ddtrace` installed before using this extension.

```
pip install ddtrace
```

</Note>

## Usage example:

```python
import strawberry
from strawberry.extensions.tracing import DatadogTracingExtension

schema = strawberry.Schema(
    Query,
    extensions=[
        DatadogTracingExtension,
    ]
)
```

<Note>

If you are not running in an Async context then you'll need to use the sync
version:

```python
import strawberry
from strawberry.extensions.tracing import DatadogTracingExtensionSync

schema = strawberry.Schema(
    Query,
    extensions=[
        DatadogTracingExtensionSync,
    ]
)
```

</Note>

---
title: Datadog
summary: Add Datadog tracing to your GraphQL server.
tags: tracing
---

# `DatadogExtension`

This extension adds support for tracing with Datadog.

<Note>

Make sure you have `ddtrace` installed before using this extension.

```shell
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
    ],
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
    ],
)
```

</Note>

## API reference:

_No arguments_

## Extending the extension

### Overriding the `create_span` method

You can customize any of the spans or add tags to them by overriding the
`create_span` method.

Example:

```python
from ddtrace import Span

from strawberry.extensions import LifecycleStep
from strawberry.extensions.tracing import DatadogTracingExtension


class DataDogExtension(DatadogTracingExtension):
    def create_span(
        self,
        lifecycle_step: LifecycleStep,
        name: str,
        **kwargs,
    ) -> Span:
        span = super().create_span(lifecycle_step, name, **kwargs)
        if lifecycle_step == LifecycleStep.OPERATION:
            span.set_tag("graphql.query", self.execution_context.query)
        return span
```

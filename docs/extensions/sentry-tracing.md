---
title: SentryTracingExtension
summary: Add Sentry tracing to your GraphQL server.
tags: tracing
---

# `SentryTracingExtension`

This extension adds support for tracing with Sentry.

## Usage example:

```python
import strawberry
from strawberry.extensions.tracing import SentryTracingExtension

schema = strawberry.Schema(
    Query,
    extensions=[
        SentryTracingExtension,
    ],
)
```

<Note>

If you are not running in an Async context then you'll need to use the sync
version:

```python
import strawberry
from strawberry.extensions.tracing import SentryTracingExtensionSync

schema = strawberry.Schema(
    Query,
    extensions=[
        SentryTracingExtensionSync,
    ],
)
```

</Note>

## API reference:

_No arguments_

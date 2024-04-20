---
title: Sentry Tracing
summary: Add Sentry tracing to your GraphQL server.
tags: tracing
---

<Warning>

As of Sentry 1.32.0, Strawberry is now supported by default. This extension is
no longer necessary. For more details, please refer to the
[release notes](https://github.com/getsentry/sentry-python/releases/tag/1.32.0).

Below is the revised usage example:

```python
import sentry_sdk
from sentry_sdk.integrations.strawberry import StrawberryIntegration

sentry_sdk.init(
    dsn="___PUBLIC_DSN___",
    integrations=[
        # make sure to set async_execution to False if you're executing
        # GraphQL queries synchronously
        StrawberryIntegration(async_execution=True),
    ],
    traces_sample_rate=1.0,
)
```

</Warning>

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

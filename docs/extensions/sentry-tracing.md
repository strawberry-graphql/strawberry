---
title: Sentry Tracing
summary: Add Sentry tracing to your GraphQL server.
tags: tracing
---

# `SentryTracingExtension`

<Warning>

As of Sentry 1.32.0, Strawberry is officially supported by the Sentry SDK.
Therefore, Strawberry's `SentryTracingExtension` has been deprecated in version
0.210.0 and finally removed with Strawberry 0.249.0 in favor of the official
Sentry SDK integration.

For more details, please refer to the
[documentation for the official Sentry Strawberry integration](https://docs.sentry.io/platforms/python/integrations/strawberry/).

</Warning>

## Filtering input coercion errors

The official Sentry integration captures all errors returned in a GraphQL
response. If invalid client input should not be reported, use Sentry's
`before_send` callback to filter `StrawberryInputCoercionError`:

```python
from typing import Any

import sentry_sdk

from strawberry.exceptions import StrawberryInputCoercionError


def before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    exc_info = hint.get("exc_info")
    error = exc_info[1] if exc_info else None

    if isinstance(error, StrawberryInputCoercionError) or isinstance(
        getattr(error, "original_error", None), StrawberryInputCoercionError
    ):
        return None

    return event


sentry_sdk.init(before_send=before_send)
```

Checking `original_error` is necessary because graphql-core wraps scalar errors
raised while coercing variables in another `GraphQLError`. For this reason,
Sentry's `ignore_errors` option alone does not filter every input coercion
error.

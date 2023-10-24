Release type: minor

This release deprecates our `SentryTracingExtension`, as it is now incorporated directly into Sentry itself as of [version 1.32.0](https://github.com/getsentry/sentry-python/releases/tag/1.32.0). You can now directly instrument Strawberry with Sentry.

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

Many thanks to @sentrivana for their work on this integration!

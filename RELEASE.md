Release type: minor

After a year-long deprecation period, the `SentryTracingExtension` has been
removed in favor of the official Sentry SDK integration.

To migrate, remove the `SentryTracingExtension` from your Strawberry schema and
then follow the
[official Sentry SDK integration guide](https://docs.sentry.io/platforms/python/integrations/strawberry/).

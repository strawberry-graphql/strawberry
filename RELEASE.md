---
release type: minor
---

This release adds a `record_exception_filter` option to `OpenTelemetryExtension`
and `OpenTelemetryExtensionSync`, to choose which resolver exceptions are
recorded on spans.

For example, it can skip permission denials, so they no longer show up as
errors in tracing backends:

```python
OpenTelemetryExtension(
    record_exception_filter=lambda error: not isinstance(error, StrawberryGraphQLError)
)
```

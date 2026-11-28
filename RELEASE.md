---
release type: minor
---

This release adds a `record_exception_filter` option to `OpenTelemetryExtension`
and `OpenTelemetryExtensionSync`, to choose which resolver exceptions are
recorded on spans.

For example, it can skip permission denials, so they no longer show up as
errors in tracing backends:

```python
class PermissionDeniedError(StrawberryGraphQLError): ...


class IsAdmin(BasePermission):
    message = "Not allowed"
    error_class = PermissionDeniedError

    def has_permission(self, source, info, **kwargs) -> bool:
        return False


OpenTelemetryExtension(
    record_exception_filter=lambda error: not isinstance(error, PermissionDeniedError)
)
```

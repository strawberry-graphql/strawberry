Release type: patch

This release adds support for custom classes inside the OpenTelemetry integration.
With this, we shouldn't see errors like this anymore:

```Invalid type dict for attribute 'graphql.param.paginator' value. Expected one of ['bool', 'str', 'bytes', 'int', 'float'] or a sequence of those types.```

Release type: patch

Description:
Fixed a bug in the OpenTelemetryExtension class where the _span_holder dictionary was incorrectly shared across all instances. This was caused by defining _span_holder as a class-level attribute with a mutable default value (dict()).

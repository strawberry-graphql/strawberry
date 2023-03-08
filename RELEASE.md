Release type: patch

This release improves how we log arguments in the OpenTelemetry extension, now
values are ignored if they are `None` and are serialized as JSON if they are
dictionaries.

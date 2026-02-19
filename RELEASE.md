Release type: patch

Fix false-positive `DuplicatedTypeName` error when two different `StrawberryObjectDefinition` instances share the same `origin` class. This can happen when third-party decorators (e.g. strawberry-django's `filter_type`) re-process a type, creating a new definition while keeping the same Python class as origin.

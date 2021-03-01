Release type: minor

# New Features
Added support for sanic webserver.

# Changelog
Deprecated the following type annotation,
```python
from strawberry.schema.base import ExecutionResult # Deprecated
```

It is now instead only supported under `strawberry.types`.

```python
from strawberry.types import ExecutionResult
```

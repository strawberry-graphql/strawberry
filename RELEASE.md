Release type: minor

# New Features
Added support for sanic webserver.

# Changelog
`ExecutionResult` was erroneously defined twice in the repository. The entry in `strawberry.schema.base` has been removed. If you were using it, switch to using
`strawberry.types.ExecutionResult` instead:

```python
from strawberry.types import ExecutionResult

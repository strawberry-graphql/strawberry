Release type: patch

This release fixes an issue with mypy when doing the following:

```python
import strawberry

@strawberry.type
class User:
    name: str = strawberry.field(description='Example')
```

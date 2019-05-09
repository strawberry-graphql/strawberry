Release Type: minor

Added support for renaming fields. Example usage:


```python
@strawberry.type
class Query:
    example: str = strawberry.field(name='test')
```


Release type: minor

This release adds support for decimal type, example:


```python
@strawberry.type
class Query:
    @strawberry.field
    def example_decimal(self) -> Decimal:
        return Decimal("3.14159")
```

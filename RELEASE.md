Release type: minor

Fixed issue that was prevent usage of InitVars.
Now you can safely use InitVar to prevent fields from showing up in the schema:


```python
@strawberry.type
class Category:
    name: str
    id: InitVar[str]

@strawberry.type
class Query:
    @strawberry.field
    def category(self, info) -> Category:
        return Category(name="example", id="123")
```


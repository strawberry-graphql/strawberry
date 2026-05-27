Release type: minor

Remove deprecated `info.field_nodes` property, deprecated since [0.73.1](https://github.com/strawberry-graphql/strawberry/releases/tag/0.73.1).

### Migration guide

**Before (deprecated):**
```python
@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        field_nodes = info.field_nodes
        ...
```

**After:**
```python
@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        selected_fields = info.selected_fields
        ...
```

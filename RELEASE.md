Release type: minor

Remove deprecated argument name-based matching for `info` and `directive_value` parameters, deprecated since [0.159.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.159.0).

### Migration guide

Parameters named `info` or `directive_value` are no longer automatically recognized by name. You must use explicit type annotations.

**Before (deprecated):**
```python
@strawberry.type
class Query:
    @strawberry.field
    def example(self, info) -> str:
        return info.context["key"]
```

**After:**
```python
@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: strawberry.Info) -> str:
        return info.context["key"]
```

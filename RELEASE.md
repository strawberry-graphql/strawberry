Release type: minor

Remove deprecated `fields` parameter from Pydantic decorators, deprecated since [0.82.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.82.0).

### Migration guide

**Before (deprecated):**
```python
@strawberry.experimental.pydantic.type(model=UserModel, fields=["name", "age"])
class User:
    pass
```

**After:**
```python
@strawberry.experimental.pydantic.type(model=UserModel)
class User:
    name: strawberry.auto
    age: strawberry.auto
```

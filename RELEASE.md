Release type: minor

This release adds support for `type[strawberry.UNSET]` in addition to `strawberry.types.unset.UnsetType` for annotations.


```python
@strawberry.type
class User:
    name: str | None = UNSET
    age: int | None | type[strawberry.UNSET] = UNSET
```

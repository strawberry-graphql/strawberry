Release type: patch

This release fixes `@strawberry.experimental.pydantic.type` and adds support for the metadata attribute on fields.

Example:
```python
@strawberry.experimental.pydantic.type(model=User)
class UserType:
    private: strawberry.auto = strawberry.field(metadata={"admin_only": True})
    public: strawberry.auto
```

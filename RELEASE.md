Release type: patch

The recent addition of support for the metadata attribute for fields isn't handled for Pydantic support.
This ensures that the metadata attribute on fields isn't lost when a @strawberry.experimental.pydantic.type
is created.

Example:
```python
@strawberry.experimental.pydantic.type(model=User)
class UserType:
    private: strawberry.auto = strawberry.field(metadata={"admin_only": True})
    public: strawberry.auto
```

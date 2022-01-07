Release type: patch

 This release checks for AutoFieldsNotInBaseModelError when converting from pydantic models.
 It is raised when strawberry.auto is used, but the pydantic model does not have
the particular field defined.

```python
class User(BaseModel):
    age: int

@strawberry.experimental.pydantic.type(User)
class UserType:
    age: strawberry.auto
    password: strawberry.auto
```

Previously no errors would be raised, and the password field would not appear on graphql schema.
Such mistakes could be common during refactoring. Now, AutoFieldsNotInBaseModelError is raised.

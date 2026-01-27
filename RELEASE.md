Release type: patch

This release fixes an issue with experimental pydantic types:

**Private fields in `from_pydantic()`**: `strawberry.Private` fields can now be populated via the `extra` dict parameter in `from_pydantic()`. Previously, private fields were ignored in the extra dict, making it impossible to set them when converting from pydantic models.

Example:

```python
class UserModel(BaseModel):
    name: str
    age: int



@pyd_type(model=UserModel)
class User:
    name: strawberry.auto
    age: strawberry.auto
    # Private field - not in GraphQL schema but stored on instance
    session_token: strawberry.Private[str]


# Convert from pydantic, providing private field via extra dict
pydantic_user = UserModel(name="Alice", age=30)
strawberry_user = User.from_pydantic(pydantic_user, extra={"session_token": "abc123"})

# Private field is accessible in resolvers
print(strawberry_user.session_token)  # "abc123"
```

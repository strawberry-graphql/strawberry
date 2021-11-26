Release type: minor

This release improves type checking support for `strawberry.union` and now allows
to use unions without any type issue, like so:

```python
@strawberry.type
class User:
    name: str

@strawberry.type
class Error:
    message: str

UserOrError = strawberry.union("UserOrError", (User, Error))

x: UserOrError = User(name="Patrick")
```

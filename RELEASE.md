Release type: patch

Fix `NameError` when using `strawberry.Parent` with forward references on
Python 3.14+ (PEP 649).

On Python 3.14, annotations are lazily evaluated via `__annotate__` (PEP 649).
When a resolver references a type via `strawberry.Parent[SomeType]` and
`SomeType` is defined after the resolver, `inspect.Signature.from_callable()`
triggers annotation evaluation which raises `NameError`. Strawberry now falls
back to `inspect.Format.FORWARDREF` to handle this gracefully.

For example, the following code now works on Python 3.14+:

```python
import strawberry

# Resolver defined before the class it references
def get_full_name(user: strawberry.Parent[User]) -> str:
    return f"{user.first_name} {user.last_name}"

@strawberry.type
class User:
    first_name: str
    last_name: str
    full_name: str = strawberry.field(resolver=get_full_name)
```

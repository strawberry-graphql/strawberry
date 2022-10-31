Release type: minor

This release adds support for generic in arguments, see the following example:

```python
T = TypeVar('T')

@strawberry.type
class Node(Generic[T]):
   @strawberry.field
   def data(self, arg: T) -> T:  # `arg` is also generic
       return arg
```

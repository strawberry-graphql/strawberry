Release type: patch

Type definitions resolve generic inputs.
 ```python
T = TypeVar('T')

@strawberry.type
class Node(Generic[T]):
    @strawberry.field
    def data(self, arg: T) -> T:  # `arg` is also generic
        return arg
```

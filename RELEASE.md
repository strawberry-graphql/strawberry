Release type: patch

 This release fixes support for generics in arguments, see the following example:

 ```python
 T = TypeVar('T')

 @strawberry.type
 class Node(Generic[T]):
    @strawberry.field
    def data(self, arg: T) -> T:  # `arg` is also generic
        return arg
 ```

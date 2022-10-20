Release type: patch

Generic scalars use the GraphQL scalar name instead of the Python class name.
 ```python
@strawberry.type
class Output(Generic[T]):
    data: T
```
`Output[str]` would be named `StringOutput` in the schema.

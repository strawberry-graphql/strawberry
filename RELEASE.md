Release type: minor

This release adds support for using strawberry.union with generics, like in this
example:

```python
@strawberry.type
class ObjectQueries[T]:
    @strawberry.field
    def by_id(
        self, id: strawberry.ID
    ) -> Union[T, Annotated[NotFoundError, strawberry.union("ByIdResult")]]: ...


@strawberry.type
class Query:
    @strawberry.field
    def some_type_queries(self, id: strawberry.ID) -> ObjectQueries[SomeType]: ...
```

which, now, creates a correct union type named `SomeTypeByIdResult`

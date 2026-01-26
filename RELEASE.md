Release type: patch

Fix nested generics with resolver-backed fields to avoid duplicate type names.

Example (previously raised `DuplicatedTypeName`):

```python
import strawberry


@strawberry.type
class Collection[T]:
    field1: list[T] = strawberry.field(resolver=lambda: [])


@strawberry.type
class Container[T]:
    items: list[T]


@strawberry.type
class TypeA: ...


@strawberry.type
class TypeB: ...


@strawberry.type
class Query:
    @strawberry.field
    def a(self) -> Container[Collection[TypeA]]: ...

    @strawberry.field
    def b(self) -> Container[Collection[TypeB]]: ...


strawberry.Schema(query=Query)
```

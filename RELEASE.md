Release type: patch

Fix `@requires(fields: ["email"])` and `@provides(fields: ["name"])` usage on a Federation field

You can use `@requires` to specify which fields you need to resolve a field

```python
import strawberry

@strawberry.federation.type(keys=["id"], extend=True)
class Product:
    id: strawberry.ID = strawberry.federation.field(external=True)
    code: str = strawberry.federation.field(external=True)

    @classmethod
    def resolve_reference(cls, id: strawberry.ID, code: str):
        return cls(id=id, code=code)

    @strawberry.federation.field(requires=["code"])
    def my_code(self) -> str:
        return self.code
```

`@provides` can be used to specify what fields are going to be resolved
by the service itself without having the Gateway to contact the external service
to resolve them.

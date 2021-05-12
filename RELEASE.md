Release type: patch

Fix `@requires(fields: ["email"])` usage on a Federation field

You can use `@requires` to specify which field your resolver needs

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

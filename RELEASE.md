Release type: minor

This releases adds experimental support for apollo federation.

Here's an example:

```python
import strawberry


@strawberry.federation.type(extend=True, keys=["id"])
class Campaign:
    id: strawberry.ID = strawberry.federation.field(external=True)

    @strawberry.field
    def title(self) -> str:
        return f"Title for {self.id}"

    @classmethod
    def resolve_reference(cls, id):
        return Campaign(id)


@strawberry.federation.type(extend=True)
class Query:
    @strawberry.field
    def strawberry(self) -> str:
        return "🍓"


schema = strawberry.federation.Schema(query=Query, types=[Campaign])
```

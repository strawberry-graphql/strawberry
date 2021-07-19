Release type: patch

This release fixes an issue with the federation printer that
prevented using federation directives with types that were
implementing interfaces.

This is now allowed:

```python
@strawberry.interface
class SomeInterface:
    id: strawberry.ID

@strawberry.federation.type(keys=["upc"], extend=True)
class Product(SomeInterface):
    upc: str = strawberry.federation.field(external=True)
```

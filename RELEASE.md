Release type: minor

This release adds support for Apollo Federation v2.6 which includes the `@authenticated`, `@requiresScopes`, and `@policy` directives.
As usual, we have first class support for them in the `strawberry.federation` namespace, here's an example:

```python
@strawberry.federation.type(
    authenticated=True,
    policy=[["client", "poweruser"], ["admin"]],
    requires_scopes=[["client", "poweruser"], ["admin"]],
)
class Product(SomeInterface):
    upc: str
```

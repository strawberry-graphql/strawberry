Release type: minor

This release adds support for Apollo Federation v2.7 which includes the `@authenticated`, `@requiresScopes`, `@policy` directives, as well as the `label` argument for `@override`.
As usual, we have first class support for them in the `strawberry.federation` namespace, here's an example:

```python
from strawberry.federation.schema_directives import Override


@strawberry.federation.type(
    authenticated=True,
    policy=[["client", "poweruser"], ["admin"]],
    requires_scopes=[["client", "poweruser"], ["admin"]],
)
class Product:
    upc: str = strawberry.federation.field(
        override=Override(override_from="mySubGraph", label="percent(1)")
    )
```

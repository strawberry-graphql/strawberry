Release type: minor

Update federation support for v2.6 which includes the @authenticated, @requiresScopes, and @policy directives.

```
    @strawberry.federation.type(
        authenticated=True,
        policy=[["client", "poweruser"], ["admin"]],
        requires_scopes=[["client", "poweruser"], ["admin"]]
    )
    class Product(SomeInterface):
        upc: str
```

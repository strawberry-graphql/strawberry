Release type: patch

This release adds support for the info param in resolve_reference:

```python
@strawberry.federation.type(keys=["upc"])
class Product:
    upc: str
    info: str

    @classmethod
    def resolve_reference(cls, info, upc):
        return Product(upc, info)
```

> Note: resolver reference is used when using Federation, similar to [Apollo server's __resolveReference](https://apollographql.com/docs/federation/api/apollo-federation/#__resolvereference)

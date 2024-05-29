Release type: minor

This release refactors our Federation integration to create types using
Strawberry directly, instead of using low level types from GraphQL-core.

The only user facing change is that now the `info` object passed to the
`resolve_reference` function is the `strawberry.Info` object instead of the one
coming coming from GraphQL-core. This is a **breaking change** for users that
were using the `info` object directly.

If you need to access the original `info` object you can do so by accessing the
`_raw_info` attribute.

```python
import strawberry


@strawberry.federation.type(keys=["upc"])
class Product:
    upc: str

    @classmethod
    def resolve_reference(cls, info: strawberry.Info, upc: str) -> "Product":
        # Access the original info object
        original_info = info._raw_info

        return Product(upc=upc)
```

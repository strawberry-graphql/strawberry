Release type: patch

This release adds support for an implicit `resolve_reference` method
on Federation type. This method will automatically create a Strawberry
instance for a federation type based on the input data received, for
example, the following:

```python
@strawberry.federation.type(keys=["id"])
class Something:
    id: str

@strawberry.federation.type(keys=["upc"])
class Product:
    upc: str
    something: Something

    @staticmethod
    def resolve_reference(**data):
        return Product(
            upc=data["upc"], something=Something(id=data["something_id"])
        )
```

doesn't need the resolve_reference method anymore.

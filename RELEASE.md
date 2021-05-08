Release type: patch

This release adds support for the info param in resolve_reference:

``````python
@strawberry.federation.type(keys=["upc"])
class Product:
    upc: str
    info: str

    @classmethod
    def resolve_reference(cls, info, upc):
        return Product(upc, info)

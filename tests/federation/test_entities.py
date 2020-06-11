import typing

import strawberry


def test_fetch_entities():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        def resolve_reference(cls, upc):
            return Product(upc)

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, info, first: int) -> typing.List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [{"__typename": "Product", "upc": "B00005N5PF"}]
        },
    )

    assert not result.errors

    assert result.data == {"_entities": [{"upc": "B00005N5PF"}]}

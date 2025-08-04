import typing

from pydantic import BaseModel

import strawberry
from strawberry.federation.schema_directives import Key


def test_fetch_entities_pydantic():
    class ProductInDb(BaseModel):
        upc: str
        name: str

    # @strawberry.federation.type(keys=["upc"])
    @strawberry.experimental.pydantic.type(
        model=ProductInDb, directives=[Key(fields="upc", resolvable=True)]
    )
    class Product:
        upc: str
        name: str

        @classmethod
        def resolve_reference(cls, upc) -> "Product":
            return Product(upc=upc, name="")

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

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

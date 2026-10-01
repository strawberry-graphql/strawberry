import pydantic

import strawberry
from strawberry.federation.schema_directives import Key


def test_entities_are_built_with_pydantic():
    @strawberry.pydantic.type(directives=[Key(fields="productId")])
    class Product(pydantic.BaseModel):
        product_id: strawberry.ID = pydantic.Field(alias="productId")
        name: str = "Jam"

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self) -> Product:
            return Product(productId=strawberry.ID("1"))

    schema = strawberry.federation.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            _entities(representations: [{ __typename: "Product", productId: "1" }]) {
                ... on Product { productId name }
            }
        }
        """
    )

    assert not result.errors
    assert result.data == {"_entities": [{"productId": "1", "name": "Jam"}]}

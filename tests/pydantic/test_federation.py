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


def test_entities_missing_a_required_field_report_it_as_missing():
    class Dimensions(pydantic.BaseModel):
        width: int
        height: int

    strawberry.pydantic.type(Dimensions)

    @strawberry.pydantic.type(directives=[Key(fields="productId")])
    class Product(pydantic.BaseModel):
        product_id: strawberry.ID = pydantic.Field(alias="productId")
        name: str
        description: str | None
        dimensions: Dimensions | None = None

    @strawberry.type
    class Query:
        product: Product | None = None

    schema = strawberry.federation.Schema(query=Query)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product { productId name description }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [
                {"__typename": "Product", "productId": "1", "name": "Jam"},
                {"__typename": "Product", "productId": "2"},
                {
                    "__typename": "Product",
                    "productId": "3",
                    "name": "Box",
                    "dimensions": {"width": 1},
                },
            ]
        },
    )

    assert result.data == {
        "_entities": [
            {"productId": "1", "name": "Jam", "description": None},
            None,
            None,
        ]
    }
    assert result.errors is not None
    assert [error.extensions for error in result.errors] == [
        {
            "validationErrors": [
                {
                    "location": ["representations", "1", "name"],
                    "message": "Field required",
                    "type": "missing",
                }
            ]
        },
        {
            "validationErrors": [
                {
                    "location": ["representations", "2", "dimensions", "height"],
                    "message": "Field required",
                    "type": "missing",
                }
            ]
        },
    ]

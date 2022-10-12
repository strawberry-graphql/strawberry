import typing

import strawberry


def test_fetch_entities():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        def resolve_reference(cls, upc):
            return Product(upc=upc)

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:
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


def test_info_param_in_resolve_reference():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        info: str

        @classmethod
        def resolve_reference(cls, info, upc):
            return Product(upc=upc, info=info)

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                    info
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

    assert (
        "GraphQLResolveInfo(field_name='_entities', field_nodes=[FieldNode"
        in result.data["_entities"][0]["info"]
    )

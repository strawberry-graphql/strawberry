import textwrap
from typing import Annotated

import strawberry
from tests.types.shared_annotated_field import shop
from tests.types.shared_annotated_field.shop import Shop
from tests.types.shared_annotated_field.warehouse import Warehouse


def test_shared_annotated_field_resolves_graphql_type_in_each_module():
    @strawberry.type
    class Query:
        shop: Shop
        warehouse: Warehouse

    schema = strawberry.Schema(query=Query)

    expected = """
    type Query {
      shop: Shop!
      warehouse: Warehouse!
    }

    type Shop {
      address: ShopAddress!
    }

    type ShopAddress {
      street: String!
    }

    type Warehouse {
      address: WarehouseAddress!
    }

    type WarehouseAddress {
      dock: Int!
    }
    """

    assert str(schema) == textwrap.dedent(expected).strip()


@strawberry.type(name="LocalAddress")
class Address:
    floor: int


def test_annotated_field_ignores_the_namespace_set_on_the_shared_annotation():
    address_field = strawberry.field(graphql_type="Address")
    # e.g. set by another type using the same `strawberry.field()`
    assert address_field.type_annotation is not None
    address_field.type_annotation.namespace = vars(shop)

    @strawberry.type
    class Office:
        address: Annotated[str, address_field]

    @strawberry.type
    class Query:
        office: Office

    schema = strawberry.Schema(query=Query)

    assert "address: LocalAddress!" in str(schema)

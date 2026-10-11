import textwrap

import strawberry
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

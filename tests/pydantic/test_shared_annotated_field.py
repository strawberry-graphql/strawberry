from typing import get_args

import strawberry
from strawberry.types.field import StrawberryField
from tests.pydantic.shared_annotated_field.aliases import AddressField
from tests.pydantic.shared_annotated_field.shop import Shop
from tests.pydantic.shared_annotated_field.warehouse import Warehouse


def test_shared_annotated_field_resolves_graphql_type_in_each_module():
    @strawberry.type
    class Query:
        shop: Shop
        warehouse: Warehouse

    schema = str(strawberry.Schema(query=Query))

    assert "type Shop {\n  address: ShopAddress!\n}" in schema
    assert "type Warehouse {\n  address: WarehouseAddress!\n}" in schema


def test_shared_annotated_field_is_not_changed():
    # other types using the alias, like `@strawberry.type`s, resolve it too
    [shared_field] = [
        arg for arg in get_args(AddressField) if isinstance(arg, StrawberryField)
    ]

    assert shared_field.type_annotation is not None
    assert shared_field.type_annotation.namespace is None

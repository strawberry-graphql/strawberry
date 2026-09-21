from typing import Annotated

import strawberry
from strawberry.federation.schema_directives import External
from strawberry.types import get_object_definition


def test_type():
    @strawberry.federation.type(keys=["id"])
    class Location:
        id: strawberry.ID

    assert Location(id=strawberry.ID("1")).id == "1"


def test_type_and_override():
    @strawberry.federation.type(keys=["id"])
    class Location:
        id: strawberry.ID
        address: str = strawberry.federation.field(override="start")

    location = Location(id=strawberry.ID("1"), address="ABC")

    assert location.id == "1"
    assert location.address == "ABC"


def test_type_and_override_with_resolver():
    @strawberry.federation.type(keys=["id"])
    class Location:
        id: strawberry.ID
        address: str = strawberry.federation.field(
            override="start", resolver=lambda: "ABC"
        )

    location = Location(id=strawberry.ID("1"))

    assert location.id == "1"


def test_annotated_federation_field():
    @strawberry.federation.type
    class Product:
        sku: Annotated[
            str,
            strawberry.federation.field(external=True, default="default-sku"),
        ]

    field = get_object_definition(Product).fields[0]

    assert Product().sku == "default-sku"
    assert any(isinstance(directive, External) for directive in field.directives)

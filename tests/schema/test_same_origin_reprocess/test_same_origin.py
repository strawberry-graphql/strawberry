from typing import TYPE_CHECKING, Annotated

import strawberry


def test_no_false_positive_duplicate_for_same_origin():
    """Test that we have no false-positive DuplicatedTypeName.

    A lazy import triggers mid-construction, which re-decorates the Fruit class
    (simulating what strawberry-django's filter_type does). This replaces
    Fruit.__strawberry_definition__ with a new instance after the original was
    already cached in the schema converter's type_map, causing two different
    StrawberryObjectDefinition objects with the same origin to be compared.
    """

    if TYPE_CHECKING:
        from tests.schema.test_same_origin_reprocess.reprocess import FruitBowl

    from tests.schema.test_same_origin_reprocess.type_fruit import Fruit

    @strawberry.type
    class Query:
        fruit: Fruit
        bowl: Annotated[
            "FruitBowl",
            strawberry.lazy("tests.schema.test_same_origin_reprocess.reprocess"),
        ]

    strawberry.Schema(query=Query)

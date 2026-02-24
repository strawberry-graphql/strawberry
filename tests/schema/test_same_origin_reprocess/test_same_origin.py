import sys
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


def test_no_false_positive_duplicate_after_module_reimport():
    """No false-positive DuplicatedTypeName after module reimport.

    When sys.modules is cleared and a module is reimported, new class objects
    are created with different id(), so the `origin is` check alone is not
    enough — we fall back to comparing __qualname__ and __module__.
    """

    if TYPE_CHECKING:
        from tests.schema.test_same_origin_reprocess.reprocess import FruitBowl

    # 1. First import: creates the original Fruit class and caches the module
    from tests.schema.test_same_origin_reprocess.type_fruit import Fruit

    original_fruit = Fruit

    # 2. Evict only the helper modules (not the test module itself) from
    #    sys.modules so that the lazy import during schema construction
    #    triggers a *fresh* import, producing new class objects with different id().
    evict = [
        "tests.schema.test_same_origin_reprocess.type_fruit",
        "tests.schema.test_same_origin_reprocess.reprocess",
    ]
    saved = {k: sys.modules.pop(k) for k in evict if k in sys.modules}

    try:

        @strawberry.type
        class Query:
            # Uses the ORIGINAL Fruit class (cached in type_map first)
            fruit: original_fruit
            # Lazy import will re-import reprocess → re-import type_fruit
            # → create a NEW Fruit class with a different id()
            bowl: Annotated[
                "FruitBowl",
                strawberry.lazy("tests.schema.test_same_origin_reprocess.reprocess"),
            ]

        # This should NOT raise DuplicatedTypeName
        strawberry.Schema(query=Query)
    finally:
        # Clean up: remove the re-imported modules and restore originals
        for k in evict:
            sys.modules.pop(k, None)
        sys.modules.update(saved)

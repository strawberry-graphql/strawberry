from enum import Enum
from typing import Optional, TypeVar, Union

from asgiref.sync import sync_to_async

import strawberry
from strawberry.types.fields.resolver import StrawberryResolver


def test_enum():
    @strawberry.enum
    class Language(Enum):
        ENGLISH = "english"
        ITALIAN = "italian"
        JAPANESE = "japanese"

    def get_spoken_language() -> Language:
        return Language.ENGLISH

    resolver = StrawberryResolver(get_spoken_language)
    # TODO: Remove reference to ._enum_definition with StrawberryEnum
    assert resolver.type is Language._enum_definition


def test_forward_references():
    global FutureUmpire

    def get_sportsball_official() -> "FutureUmpire":
        return FutureUmpire("ref")  # noqa: F821

    @strawberry.type
    class FutureUmpire:
        name: str

    resolver = StrawberryResolver(get_sportsball_official)
    assert resolver.type is FutureUmpire

    del FutureUmpire


def test_list():
    def get_collection_types() -> list[str]:
        return ["list", "tuple", "dict", "set"]

    resolver = StrawberryResolver(get_collection_types)
    assert resolver.type == list[str]


def test_literal():
    def version() -> float:
        return 1.0

    resolver = StrawberryResolver(version)
    assert resolver.type is float


def test_object():
    @strawberry.type
    class Polygon:
        edges: int
        faces: int

    def get_2d_object() -> Polygon:
        return Polygon(12, 6)

    resolver = StrawberryResolver(get_2d_object)
    assert resolver.type is Polygon


def test_optional():
    def stock_market_tool() -> Optional[str]: ...

    resolver = StrawberryResolver(stock_market_tool)
    assert resolver.type == Optional[str]


def test_type_var():
    T = TypeVar("T")

    def caffeinated_drink() -> T: ...

    resolver = StrawberryResolver(caffeinated_drink)
    assert resolver.type == T


def test_union():
    @strawberry.type
    class Venn:
        foo: int

    @strawberry.type
    class Diagram:
        bar: float

    def get_overlap() -> Union[Venn, Diagram]: ...

    resolver = StrawberryResolver(get_overlap)
    assert resolver.type == Union[Venn, Diagram]


def test_sync_to_async_resolver():
    @sync_to_async
    def async_resolver() -> str:
        return "patrick"

    resolver = StrawberryResolver(async_resolver)
    assert resolver.is_async

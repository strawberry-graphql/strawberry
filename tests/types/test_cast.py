import strawberry
from strawberry.types.cast import get_strawberry_type_cast


def test_cast():
    @strawberry.type
    class SomeType: ...

    class OtherType: ...

    obj = OtherType
    assert get_strawberry_type_cast(obj) is None

    cast_obj = strawberry.cast(SomeType, obj)
    assert cast_obj is obj
    assert get_strawberry_type_cast(cast_obj) is SomeType


def test_cast_none_obj():
    @strawberry.type
    class SomeType: ...

    obj = None
    assert get_strawberry_type_cast(obj) is None

    cast_obj = strawberry.cast(SomeType, obj)
    assert cast_obj is None
    assert get_strawberry_type_cast(obj) is None

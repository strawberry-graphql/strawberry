# ruff: noqa: F821

import pytest

import strawberry
from strawberry.utils.inspect import get_specialized_type_var_map


@pytest.mark.parametrize("value", [object, type(None), int, str, type("Foo", (), {})])
def test_get_specialized_type_var_map_non_generic(value: type):
    assert get_specialized_type_var_map(value) is None


def test_get_specialized_type_var_map_generic_not_specialized():
    @strawberry.type
    class Foo[T]: ...

    assert get_specialized_type_var_map(Foo) == {}


def test_get_specialized_type_var_map_generic():
    @strawberry.type
    class Foo[T]: ...

    @strawberry.type
    class Bar(Foo[int]): ...

    assert get_specialized_type_var_map(Bar) == {"T": int}


def test_get_specialized_type_var_map_from_alias():
    @strawberry.type
    class Foo[T]: ...

    SpecializedFoo = Foo[int]

    assert get_specialized_type_var_map(SpecializedFoo) == {"T": int}


def test_get_specialized_type_var_map_from_alias_with_inheritance():
    @strawberry.type
    class Foo[T]: ...

    SpecializedFoo = Foo[int]

    @strawberry.type
    class Bar(SpecializedFoo): ...

    assert get_specialized_type_var_map(Bar) == {"T": int}


def test_get_specialized_type_var_map_generic_subclass():
    @strawberry.type
    class Foo[T]: ...

    @strawberry.type
    class Bar(Foo[int]): ...

    @strawberry.type
    class BarSubclass(Bar): ...

    assert get_specialized_type_var_map(BarSubclass) == {"T": int}


def test_get_specialized_type_var_map_double_generic():
    @strawberry.type
    class Foo[T]: ...

    @strawberry.type
    class Bar[T](Foo[T]): ...

    @strawberry.type
    class Bin(Bar[int]): ...

    assert get_specialized_type_var_map(Bin) == {"T": int}


def test_get_specialized_type_var_map_double_generic_subclass():
    @strawberry.type
    class Foo[T]: ...

    @strawberry.type
    class Bar[T](Foo[T]): ...

    @strawberry.type
    class Bin(Bar[int]): ...

    @strawberry.type
    class BinSubclass(Bin): ...

    assert get_specialized_type_var_map(Bin) == {"T": int}


def test_get_specialized_type_var_map_double_generic_passthrough():
    @strawberry.type
    class Foo[T]: ...

    @strawberry.type
    class Bar[K](Foo[K]): ...

    @strawberry.type
    class Bin(Bar[int]): ...

    assert get_specialized_type_var_map(Bin) == {
        "T": int,
        "K": int,
    }


def test_get_specialized_type_var_map_multiple_inheritance():
    @strawberry.type
    class Foo[T]: ...

    @strawberry.type
    class Bar[K]: ...

    @strawberry.type
    class Bin(Foo[int]): ...

    @strawberry.type
    class Baz(Bin, Bar[str]): ...

    assert get_specialized_type_var_map(Baz) == {
        "T": int,
        "K": str,
    }


def test_get_specialized_type_var_map_multiple_inheritance_subclass():
    @strawberry.type
    class Foo[T]: ...

    @strawberry.type
    class Bar[K]: ...

    @strawberry.type
    class Bin(Foo[int]): ...

    @strawberry.type
    class Baz(Bin, Bar[str]): ...

    @strawberry.type
    class BazSubclass(Baz): ...

    assert get_specialized_type_var_map(BazSubclass) == {
        "T": int,
        "K": str,
    }

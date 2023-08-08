# ruff: noqa: F821

import pytest

import strawberry
from strawberry.utils.inspect import get_specialized_type_var_map


@pytest.mark.parametrize("value", [object, type(None), int, str, type("Foo", (), {})])
def test_get_specialized_type_var_map_non_generic(value: type):
    assert get_specialized_type_var_map(value) is None


def test_get_specialized_type_var_map_generic_not_specialized():
    @strawberry.type
    class Foo[_T]:
        ...

    assert get_specialized_type_var_map(Foo) == {}


def test_get_specialized_type_var_map_generic():
    @strawberry.type
    class Foo[_T]:
        ...

    @strawberry.type
    class Bar(Foo[int]):
        ...

    assert get_specialized_type_var_map(Bar) == {"_T": int}


def test_get_specialized_type_var_map_generic_subclass():
    @strawberry.type
    class Foo[_T]:
        ...

    @strawberry.type
    class Bar(Foo[int]):
        ...

    @strawberry.type
    class BarSubclass(Bar):
        ...

    assert get_specialized_type_var_map(BarSubclass) == {"_T": int}


def test_get_specialized_type_var_map_double_generic():
    @strawberry.type
    class Foo[_T]:
        ...

    @strawberry.type
    class Bar[_T](Foo[_T]):
        ...

    @strawberry.type
    class Bin(Bar[int]):
        ...

    assert get_specialized_type_var_map(Bin) == {"_T": int}


def test_get_specialized_type_var_map_double_generic_subclass():
    @strawberry.type
    class Foo[_T]:
        ...

    @strawberry.type
    class Bar[_T](Foo[_T]):
        ...

    @strawberry.type
    class Bin(Bar[int]):
        ...

    @strawberry.type
    class BinSubclass(Bin):
        ...

    assert get_specialized_type_var_map(Bin) == {"_T": int}


def test_get_specialized_type_var_map_multiple_inheritance():
    @strawberry.type
    class Foo[_T]:
        ...

    @strawberry.type
    class Bar[_K]:
        ...

    @strawberry.type
    class Bin(Foo[int]):
        ...

    @strawberry.type
    class Baz(Bin, Bar[str]):
        ...

    assert get_specialized_type_var_map(Baz) == {
        "_T": int,
        "_K": str,
    }


def test_get_specialized_type_var_map_multiple_inheritance_subclass():
    @strawberry.type
    class Foo[_T]:
        ...

    @strawberry.type
    class Bar[_K]:
        ...

    @strawberry.type
    class Bin(Foo[int]):
        ...

    @strawberry.type
    class Baz(Bin, Bar[str]):
        ...

    @strawberry.type
    class BazSubclass(Baz):
        ...

    assert get_specialized_type_var_map(BazSubclass) == {
        "_T": int,
        "_K": str,
    }

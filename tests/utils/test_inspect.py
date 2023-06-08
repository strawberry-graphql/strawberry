from typing import Generic, TypeVar

import pytest

import strawberry
from strawberry.utils.inspect import get_specialized_type_var_map

_T = TypeVar("_T")
_K = TypeVar("_K")


@pytest.mark.parametrize("value", [object, type(None), int, str, type("Foo", (), {})])
def test_get_specialized_type_var_map_non_generic(value: type):
    assert get_specialized_type_var_map(value) is None


def test_get_specialized_type_var_map_generic_not_specialized():
    @strawberry.type
    class Foo(Generic[_T]):
        ...

    assert get_specialized_type_var_map(Foo) == {}
    assert get_specialized_type_var_map(Foo, include_type_vars=True) == {_T: _T}


@pytest.mark.parametrize("include_type_vars", [True, False])
def test_get_specialized_type_var_map_generic(include_type_vars: bool):
    @strawberry.type
    class Foo(Generic[_T]):
        ...

    @strawberry.type
    class Bar(Foo[int]):
        ...

    assert get_specialized_type_var_map(Bar, include_type_vars=include_type_vars) == {
        _T: int
    }


@pytest.mark.parametrize("include_type_vars", [True, False])
def test_get_specialized_type_var_map_generic_subclass(include_type_vars: bool):
    @strawberry.type
    class Foo(Generic[_T]):
        ...

    @strawberry.type
    class Bar(Foo[int]):
        ...

    @strawberry.type
    class BarSubclass(Bar):
        ...

    assert get_specialized_type_var_map(
        BarSubclass, include_type_vars=include_type_vars
    ) == {_T: int}


@pytest.mark.parametrize("include_type_vars", [True, False])
def test_get_specialized_type_var_map_double_generic(include_type_vars: bool):
    @strawberry.type
    class Foo(Generic[_T]):
        ...

    @strawberry.type
    class Bar(Foo[_T]):
        ...

    @strawberry.type
    class Bin(Bar[int]):
        ...

    assert get_specialized_type_var_map(Bin, include_type_vars=include_type_vars) == {
        _T: int
    }


@pytest.mark.parametrize("include_type_vars", [True, False])
def test_get_specialized_type_var_map_double_generic_subclass(include_type_vars: bool):
    @strawberry.type
    class Foo(Generic[_T]):
        ...

    @strawberry.type
    class Bar(Foo[_T]):
        ...

    @strawberry.type
    class Bin(Bar[int]):
        ...

    @strawberry.type
    class BinSubclass(Bin):
        ...

    assert get_specialized_type_var_map(Bin, include_type_vars=include_type_vars) == {
        _T: int
    }


@pytest.mark.parametrize("include_type_vars", [True, False])
def test_get_specialized_type_var_map_multiple_inheritance(include_type_vars: bool):
    @strawberry.type
    class Foo(Generic[_T]):
        ...

    @strawberry.type
    class Bar(Generic[_K]):
        ...

    @strawberry.type
    class Bin(Foo[int]):
        ...

    @strawberry.type
    class Baz(Bin, Bar[str]):
        ...

    assert get_specialized_type_var_map(Baz, include_type_vars=include_type_vars) == {
        _T: int,
        _K: str,
    }


@pytest.mark.parametrize("include_type_vars", [True, False])
def test_get_specialized_type_var_map_multiple_inheritance_subclass(
    include_type_vars: bool,
):
    @strawberry.type
    class Foo(Generic[_T]):
        ...

    @strawberry.type
    class Bar(Generic[_K]):
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

    assert get_specialized_type_var_map(
        BazSubclass, include_type_vars=include_type_vars
    ) == {
        _T: int,
        _K: str,
    }

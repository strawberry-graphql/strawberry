from typing import Any, Generic, TypeVar

import pytest

import strawberry
from strawberry.utils.inspect import (
    get_generic_arguments,
    get_specialized_type_var_map,
)

_T = TypeVar("_T")
_K = TypeVar("_K")


@pytest.mark.parametrize("value", [object, type(None), int, str, type("Foo", (), {})])
def test_get_specialized_type_var_map_non_generic(value: type):
    assert get_specialized_type_var_map(value) is None


def test_get_specialized_type_var_map_generic_not_specialized():
    @strawberry.type
    class Foo(Generic[_T]): ...

    assert get_specialized_type_var_map(Foo) == {}


def test_get_specialized_type_var_map_generic():
    @strawberry.type
    class Foo(Generic[_T]): ...

    @strawberry.type
    class Bar(Foo[int]): ...

    assert get_specialized_type_var_map(Bar) == {"_T": int}


def test_get_specialized_type_var_map_from_alias():
    @strawberry.type
    class Foo(Generic[_T]): ...

    SpecializedFoo = Foo[int]

    assert get_specialized_type_var_map(SpecializedFoo) == {"_T": int}


def test_get_specialized_type_var_map_from_alias_with_inheritance():
    @strawberry.type
    class Foo(Generic[_T]): ...

    SpecializedFoo = Foo[int]

    @strawberry.type
    class Bar(SpecializedFoo): ...

    assert get_specialized_type_var_map(Bar) == {"_T": int}


def test_get_specialized_type_var_map_generic_subclass():
    @strawberry.type
    class Foo(Generic[_T]): ...

    @strawberry.type
    class Bar(Foo[int]): ...

    @strawberry.type
    class BarSubclass(Bar): ...

    assert get_specialized_type_var_map(BarSubclass) == {"_T": int}


def test_get_specialized_type_var_map_double_generic():
    @strawberry.type
    class Foo(Generic[_T]): ...

    @strawberry.type
    class Bar(Foo[_T]): ...

    @strawberry.type
    class Bin(Bar[int]): ...

    assert get_specialized_type_var_map(Bin) == {"_T": int}


def test_get_specialized_type_var_map_double_generic_subclass():
    @strawberry.type
    class Foo(Generic[_T]): ...

    @strawberry.type
    class Bar(Foo[_T]): ...

    @strawberry.type
    class Bin(Bar[int]): ...

    @strawberry.type
    class BinSubclass(Bin): ...

    assert get_specialized_type_var_map(Bin) == {"_T": int}


def test_get_specialized_type_var_map_double_generic_passthrough():
    @strawberry.type
    class Foo(Generic[_T]): ...

    @strawberry.type
    class Bar(Foo[_K], Generic[_K]): ...

    @strawberry.type
    class Bin(Bar[int]): ...

    assert get_specialized_type_var_map(Bin) == {
        "_T": int,
        "_K": int,
    }


def test_get_specialized_type_var_map_multiple_inheritance():
    @strawberry.type
    class Foo(Generic[_T]): ...

    @strawberry.type
    class Bar(Generic[_K]): ...

    @strawberry.type
    class Bin(Foo[int]): ...

    @strawberry.type
    class Baz(Bin, Bar[str]): ...

    assert get_specialized_type_var_map(Baz) == {
        "_T": int,
        "_K": str,
    }


def test_get_specialized_type_var_map_multiple_inheritance_subclass():
    @strawberry.type
    class Foo(Generic[_T]): ...

    @strawberry.type
    class Bar(Generic[_K]): ...

    @strawberry.type
    class Bin(Foo[int]): ...

    @strawberry.type
    class Baz(Bin, Bar[str]): ...

    @strawberry.type
    class BazSubclass(Baz): ...

    assert get_specialized_type_var_map(BazSubclass) == {
        "_T": int,
        "_K": str,
    }


def test_get_generic_arguments_by_base():
    class Foo(Generic[_T]): ...

    class Bar(Generic[_T]): ...

    class Bin(Foo[list[_K]], Generic[_K]): ...

    class Baz(Bin[int], Bar[str]): ...

    arguments = get_generic_arguments(Baz)

    assert arguments[Baz] == {}
    assert arguments[Bin] == {_K: int}
    assert arguments[Foo] == {_T: list[int]}
    assert arguments[Bar] == {_T: str}


def test_get_generic_arguments_of_an_alias():
    class Foo(Generic[_T]): ...

    assert get_generic_arguments(Foo[int])[Foo] == {_T: int}


def test_get_generic_arguments_of_unspecialized_generics():
    class Foo(Generic[_T]): ...

    class Bar(Foo): ...

    assert get_generic_arguments(Bar)[Foo] == {}


def test_get_generic_arguments_with_split_base():
    class Foo(Generic[_T]): ...

    # parametrized with a subclass that keeps its arguments, like Pydantic does
    class IntFoo(Foo):
        arguments = (int,)

    class Bar(IntFoo): ...

    def split_base(base: Any) -> tuple[Any, tuple[Any, ...]]:
        if "arguments" in vars(base):
            return base.__bases__[0], base.arguments

        return base, ()

    assert get_generic_arguments(Bar, split_base)[Foo] == {_T: int}

import textwrap
from typing import Annotated, Generic, NewType, TypeVar

import pytest

import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types.base import StrawberryList, StrawberryOptional
from strawberry.types.enum import EnumDefinition
from strawberry.types.lazy_type import LazyType
from strawberry.types.union import StrawberryUnion

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


Enum = EnumDefinition(None, name="Enum", values=[], description=None)  # type: ignore
CustomInt = strawberry.scalar(NewType("CustomInt", int))


@strawberry.type
class TypeA:
    name: str


@strawberry.type
class TypeB:
    age: int


@pytest.mark.parametrize(
    ("types", "expected_name"),
    [
        ([StrawberryList(str)], "StrListExample"),
        ([StrawberryList(StrawberryList(str))], "StrListListExample"),
        ([StrawberryOptional(StrawberryList(str))], "StrListOptionalExample"),
        ([StrawberryList(StrawberryOptional(str))], "StrOptionalListExample"),
        ([StrawberryList(Enum)], "EnumListExample"),
        ([StrawberryUnion("Union", (TypeA, TypeB))], "UnionExample"),  # pyright: ignore
        ([TypeA], "TypeAExample"),
        ([CustomInt], "CustomIntExample"),
        ([TypeA, TypeB], "TypeATypeBExample"),
        ([TypeA, LazyType["TypeB", "test_names"]], "TypeATypeBExample"),  # type: ignore
        (
            [TypeA, Annotated["TypeB", strawberry.lazy("test_names")]],
            "TypeATypeBExample",
        ),
    ],
)
def test_name_generation(types, expected_name):
    config = StrawberryConfig()

    @strawberry.type
    class Example(Generic[T]):
        a: T

    type_definition = Example.__strawberry_definition__  # type: ignore

    assert config.name_converter.from_generic(type_definition, types) == expected_name


def test_nested_generics():
    config = StrawberryConfig()

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edges: list[T]

    type_definition = Connection.__strawberry_definition__  # type: ignore

    assert (
        config.name_converter.from_generic(
            type_definition,
            [
                Edge[int],
            ],
        )
        == "IntEdgeConnection"
    )


def test_nested_generics_aliases_with_schema():
    """This tests is similar to the previous test, but it also tests against
    the schema, since the resolution of the type name might be different.
    """
    config = StrawberryConfig()

    @strawberry.type
    class Value(Generic[T]):
        value: T

    @strawberry.type
    class DictItem(Generic[K, V]):
        key: K
        value: V

    type_definition = Value.__strawberry_definition__  # type: ignore

    assert (
        config.name_converter.from_generic(
            type_definition,
            [
                StrawberryList(DictItem[int, str]),
            ],
        )
        == "IntStrDictItemListValue"
    )

    @strawberry.type
    class Query:
        d: Value[list[DictItem[int, str]]]

    schema = strawberry.Schema(query=Query)

    expected = textwrap.dedent(
        """
        type IntStrDictItem {
          key: Int!
          value: String!
        }

        type IntStrDictItemListValue {
          value: [IntStrDictItem!]!
        }

        type Query {
          d: IntStrDictItemListValue!
        }
        """
    ).strip()

    assert str(schema) == expected

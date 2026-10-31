from itertools import permutations

from strawberry.codegen.query_codegen import QueryCodegenPluginManager
from strawberry.codegen.types import (
    GraphQLField,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOptional,
    GraphQLScalar,
    GraphQLType,
    GraphQLUnion,
)


def test_sort_types_preserves_collection_order_for_unrelated_types() -> None:
    types = [GraphQLObjectType(name) for name in ("C", "A", "B")]
    manager = QueryCodegenPluginManager([])

    for permutation in permutations(types):
        assert manager._sort_types(list(permutation)) == list(permutation)


def test_sort_types_respects_dependencies_before_collection_order() -> None:
    c = GraphQLObjectType("C")
    a = GraphQLObjectType("A", [GraphQLField("child", None, c)])
    b = GraphQLObjectType("B")
    manager = QueryCodegenPluginManager([])

    assert manager._sort_types([a, b, c]) == [b, c, a]
    assert manager._sort_types([a, c, b]) == [c, a, b]


def test_sort_types_considers_newly_ready_types_immediately() -> None:
    a = GraphQLObjectType("A")
    b = GraphQLObjectType("B", [GraphQLField("child", None, a)])
    c = GraphQLObjectType("C")
    manager = QueryCodegenPluginManager([])

    assert manager._sort_types([b, a, c]) == [a, b, c]


def test_sort_types_handles_wrappers_unions_and_equivalent_scalars() -> None:
    scalar = GraphQLScalar("String", str)
    a = GraphQLObjectType(
        "A", [GraphQLField("value", None, GraphQLScalar("String", str))]
    )
    b = GraphQLObjectType(
        "B", [GraphQLField("children", None, GraphQLOptional(GraphQLList(a)))]
    )
    union = GraphQLUnion("Union", [b, a])
    manager = QueryCodegenPluginManager([])
    types: list[GraphQLType] = [union, b, a, scalar]

    for permutation in permutations(types):
        assert manager._sort_types(list(permutation)) == [scalar, a, b, union]


def test_sort_types_ignores_dependencies_that_are_not_collected() -> None:
    a = GraphQLObjectType(
        "A", [GraphQLField("__typename", None, GraphQLScalar("String", None))]
    )
    manager = QueryCodegenPluginManager([])

    assert manager._sort_types([a]) == [a]


def test_sort_types_preserves_types_with_the_same_name() -> None:
    scalar = GraphQLScalar("String", str)
    a = GraphQLObjectType("Shared", [GraphQLField("value", None, scalar)])
    b = GraphQLObjectType("Shared", [GraphQLField("child", None, a)])
    manager = QueryCodegenPluginManager([])

    assert manager._sort_types([b, a, scalar]) == [scalar, a, b]


def test_sort_types_handles_empty_input() -> None:
    assert QueryCodegenPluginManager([])._sort_types([]) == []

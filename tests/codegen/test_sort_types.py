from itertools import permutations
from unittest.mock import patch

from strawberry.codegen.query_codegen import QueryCodegenPluginManager, _get_deps
from strawberry.codegen.types import (
    GraphQLField,
    GraphQLList,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLOptional,
    GraphQLScalar,
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

    assert manager._sort_types([a, b, c]) == [c, a, b]
    assert manager._sort_types([a, c, b]) == [c, a, b]


def test_sort_types_visits_dependencies_before_later_unrelated_types() -> None:
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
    types: list[GraphQLNamedType] = [union, b, a, scalar]

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
    equivalent_a = GraphQLObjectType(
        "Shared", [GraphQLField("value", None, GraphQLScalar("String", str))]
    )
    manager = QueryCodegenPluginManager([])

    for dependency in (a, equivalent_a):
        b = GraphQLObjectType("Shared", [GraphQLField("child", None, dependency)])
        assert manager._sort_types([b, a, scalar]) == [scalar, a, b]


def test_get_deps_only_returns_direct_unwrapped_dependencies() -> None:
    scalar = GraphQLScalar("String", str)
    child = GraphQLObjectType("Child", [GraphQLField("value", None, scalar)])
    parent = GraphQLObjectType(
        "Parent", [GraphQLField("children", None, GraphQLOptional(GraphQLList(child)))]
    )

    assert list(_get_deps(parent)) == [child]
    assert list(_get_deps(child)) == [scalar]
    assert list(_get_deps(scalar)) == []


def test_sort_types_visits_each_nested_type_once_without_equality_scans() -> None:
    types = [GraphQLObjectType("Leaf")]
    for index in range(128):
        types.append(
            GraphQLObjectType(
                f"Parent{index}",
                [
                    GraphQLField(
                        "children", None, GraphQLOptional(GraphQLList(types[-1]))
                    )
                ],
            )
        )

    manager = QueryCodegenPluginManager([])
    with (
        patch.object(
            GraphQLObjectType,
            "__eq__",
            side_effect=AssertionError("Nested types should be resolved by identity"),
        ),
        patch(
            "strawberry.codegen.query_codegen._get_deps", wraps=_get_deps
        ) as get_deps,
    ):
        ordered = manager._sort_types(list(reversed(types)))

    assert len(ordered) == len(types)
    assert all(
        actual is expected for actual, expected in zip(ordered, types, strict=True)
    )
    assert get_deps.call_count == len(types)


def test_sort_types_handles_empty_input() -> None:
    assert QueryCodegenPluginManager([])._sort_types([]) == []

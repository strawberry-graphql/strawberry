from typing import Iterable, Iterator, List

import pytest

import strawberry
from strawberry import relay
from strawberry.exceptions.missing_return_annotation import MissingReturnAnnotationError
from strawberry.relay.exceptions import (
    NodeIDAnnotationError,
    RelayWrongAnnotationError,
    RelayWrongNodeResolverAnnotationError,
)
from tests.relay.schema import Fruit


@strawberry.type
class NonNodeType:
    foo: str


@pytest.mark.raises_strawberry_exception(
    NodeIDAnnotationError,
    match='No field annotated with `nodeid` found in "Fruit"',
)
def test_raises_error_on_missing_node_id_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        code: str


@pytest.mark.raises_strawberry_exception(
    NodeIDAnnotationError,
    match='More than one field annotated with `NodeID` found in "Fruit"',
)
def test_raises_error_on_multiple_node_id_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        pk: relay.NodeID[str]
        code: relay.NodeID[str]


@pytest.mark.raises_strawberry_exception(
    MissingReturnAnnotationError,
    match=(
        'Return annotation missing for field "custom_resolver", '
        "did you forget to add it?"
    ),
)
def test_raises_error_on_connection_missing_annotation():
    @strawberry.type
    class Query:
        @relay.connection  # type: ignore
        def custom_resolver(self):
            ...


@pytest.mark.raises_strawberry_exception(
    RelayWrongAnnotationError,
    match=(
        'Unable to determine the connection type of field "custom_resolver". '
        r"It should be annotated with a return value of `List\[<NodeType>\]`, "
        r"`Iterable\[<NodeType>\]`, `Iterator\[<NodeType>\]`, "
        r"`AsyncIterable\[<NodeType>\]` or `AsyncIterator\[<NodeType>\]`"
    ),
)
@pytest.mark.parametrize(
    "annotation",
    [Fruit, List[int], List[object], Iterable[int], Iterator[int], List[NonNodeType]],
)
def test_raises_error_on_connection_with_wrong_annotation(annotation):
    @strawberry.type
    class Query:
        @relay.connection
        def custom_resolver(self) -> annotation:
            ...


@pytest.mark.raises_strawberry_exception(
    RelayWrongNodeResolverAnnotationError,
    match=(
        'Unable to determine the connection type of field "custom_resolver". '
        "The `node_resolver` function should be annotated with a return value "
        "of `<NodeType>`"
    ),
)
@pytest.mark.parametrize("annotation", [int, object, NonNodeType])
def test_raises_error_on_connection_with_node_resolver_missing_annotation(annotation):
    def node_converter(n: Fruit):
        ...

    @strawberry.type
    class Query:
        @relay.connection(node_converter=node_converter)  # type: ignore
        def custom_resolver(self) -> List[Fruit]:
            ...


@pytest.mark.raises_strawberry_exception(
    RelayWrongNodeResolverAnnotationError,
    match=(
        'Unable to determine the connection type of field "custom_resolver". '
        "The `node_resolver` function should be annotated with a return value "
        "of `<NodeType>`"
    ),
)
@pytest.mark.parametrize("annotation", [int, object, NonNodeType])
def test_raises_error_on_connection_with_wrong_node_resolver_annotation(annotation):
    def node_converter(n: Fruit) -> annotation:
        ...

    @strawberry.type
    class Query:
        @relay.connection(node_converter=node_converter)  # type: ignore
        def custom_resolver(self) -> List[Fruit]:
            ...

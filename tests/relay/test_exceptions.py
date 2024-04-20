from typing import List

import pytest

import strawberry
from strawberry import relay
from strawberry.relay.exceptions import (
    NodeIDAnnotationError,
    RelayWrongAnnotationError,
    RelayWrongResolverAnnotationError,
)


@strawberry.type
class NonNodeType:
    foo: str


@pytest.mark.raises_strawberry_exception(
    NodeIDAnnotationError,
    match='No field annotated with `NodeID` found in "Fruit"',
)
def test_raises_error_on_missing_node_id_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        code: str

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[Fruit])
        def fruits(self) -> List[Fruit]: ...

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    NodeIDAnnotationError,
    match='More than one field annotated with `NodeID` found in "Fruit"',
)
def test_raises_error_on_multiple_node_id_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        pk: relay.NodeID[str]
        code: relay.NodeID[str]

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[Fruit])
        def fruits(self) -> List[Fruit]: ...

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    RelayWrongAnnotationError,
    match=(
        'Wrong annotation used on field "fruits_conn". '
        'It should be annotated with a "Connection" subclass.'
    ),
)
def test_raises_error_on_connection_missing_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        pk: relay.NodeID[str]

    @strawberry.type
    class Query:
        fruits_conn: List[Fruit] = relay.connection()

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    RelayWrongAnnotationError,
    match=(
        'Wrong annotation used on field "custom_resolver". '
        'It should be annotated with a "Connection" subclass.'
    ),
)
def test_raises_error_on_connection_wrong_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        pk: relay.NodeID[str]

    @strawberry.type
    class Query:
        @relay.connection(List[Fruit])  # type: ignore
        def custom_resolver(self) -> List[Fruit]: ...

    strawberry.Schema(query=Query)


@pytest.mark.raises_strawberry_exception(
    RelayWrongResolverAnnotationError,
    match=(
        'Wrong annotation used on "custom_resolver" resolver. '
        "It should be return an iterable or async iterable object."
    ),
)
def test_raises_error_on_connection_resolver_wrong_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        pk: relay.NodeID[str]

    @strawberry.type
    class Query:
        @relay.connection(relay.Connection[Fruit])  # type: ignore
        def custom_resolver(self): ...

    strawberry.Schema(query=Query)

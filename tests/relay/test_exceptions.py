from typing import List

import pytest

import strawberry
from strawberry import Info, relay
from strawberry.relay import GlobalID
from strawberry.relay.exceptions import NodeIDAnnotationError


@strawberry.type
class NonNodeType:
    foo: str


def test_raises_error_on_unknown_node_type_in_global_id():
    @strawberry.type
    class Query:
        @strawberry.field()
        def test(self, info: Info) -> GlobalID:
            _id = GlobalID("foo", "bar")
            _id.resolve_type(info)
            return _id

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("""
        query TestQuery {
            test
        }
    """)
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "Cannot resolve. GlobalID requires a GraphQL type, received `foo`."
    )


def test_raises_error_on_non_node_type_in_global_id():
    @strawberry.type
    class Query:
        @strawberry.field()
        def test(self, info: Info) -> GlobalID:
            _id = GlobalID("NonNodeType", "bar")
            _id.resolve_type(info)
            return _id

    schema = strawberry.Schema(query=Query, types=(NonNodeType,))

    result = schema.execute_sync("""
        query TestQuery {
            test
        }
    """)
    assert len(result.errors) == 1
    assert (
        result.errors[0].message == "Cannot resolve. GlobalID requires a GraphQL Node "
        "type, received `NonNodeType`."
    )


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

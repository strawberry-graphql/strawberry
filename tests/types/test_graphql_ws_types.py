from strawberry.subscriptions.protocols.graphql_ws.types import (
    DataPayload,
    StartPayload,
)


def test_dataclass_start_payload_total_behavior():
    """
    The TypeDict class used for the graphql_ws setup utilized a total=False argument.
    This argument means that a class can be instantiated without all the values needing
    to be included
    """
    start_payload = StartPayload(query="")

    assert isinstance(start_payload, StartPayload)
    assert start_payload.query == ""
    assert start_payload.variables is None
    assert start_payload.operationName is None


def test_dataclass_data_payload_total_behavior():
    """
    The TypeDict class used for the graphql_ws setup utilized a total=False argument.
    This argument means that a class can be instantiated without all the values needing
    to be included
    """
    data_payload = DataPayload(data="")

    assert isinstance(data_payload, DataPayload)
    assert data_payload.data == ""
    assert data_payload.errors == []

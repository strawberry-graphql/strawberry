from typing import Any

import pytest

import strawberry
from strawberry.relay.types import GlobalIDValueError


@pytest.mark.parametrize("type_name", [None, 1, 1.1])
def test_global_id_wrong_type_name(type_name: Any):
    with pytest.raises(GlobalIDValueError) as exc_info:
        strawberry.relay.GlobalID(type_name=type_name, node_id="foobar")


@pytest.mark.parametrize("node_id", [None, 1, 1.1])
def test_global_id_wrong_type_node_id(node_id: Any):
    with pytest.raises(GlobalIDValueError) as exc_info:
        strawberry.relay.GlobalID(type_name="foobar", node_id=node_id)


def test_global_id_from_id():
    gid = strawberry.relay.GlobalID.from_id("Zm9vYmFyOjE=")
    assert gid.type_name == "foobar"
    assert gid.node_id == "1"


@pytest.mark.parametrize("value", ["foobar", ["Zm9vYmFy"], 123])
def test_global_id_from_id_error(value: Any):
    with pytest.raises(GlobalIDValueError) as exc_info:
        strawberry.relay.GlobalID.from_id(value)

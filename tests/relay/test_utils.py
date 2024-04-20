from typing import Any

import pytest

from strawberry.relay.utils import from_base64, to_base64
from strawberry.type import get_object_definition

from .schema import Fruit


def test_from_base64():
    type_name, node_id = from_base64("Zm9vYmFyOjE=")  # foobar:1
    assert type_name == "foobar"
    assert node_id == "1"


def test_from_base64_with_extra_colon():
    type_name, node_id = from_base64("Zm9vYmFyOjE6Mjoz")  # foobar:1:2:3
    assert type_name == "foobar"
    assert node_id == "1:2:3"


@pytest.mark.parametrize("value", [None, 1, 1.1, "dsadfas"])
def test_from_base64_non_base64(value: Any):
    with pytest.raises(ValueError):
        type_name, node_id = from_base64(value)


@pytest.mark.parametrize(
    "value",
    [
        "Zm9vYmFy",  # foobar
        "Zm9vYmFyLDE=",  # foobar,1
        "Zm9vYmFyOzE=",  # foobar;1
    ],
)
def test_from_base64_wrong_number_of_args(value: Any):
    with pytest.raises(ValueError):
        type_name, node_id = from_base64(value)


def test_to_base64():
    value = to_base64("foobar", "1")
    assert value == "Zm9vYmFyOjE="


def test_to_base64_with_type():
    value = to_base64(Fruit, "1")
    assert value == "RnJ1aXQ6MQ=="


def test_to_base64_with_typedef():
    value = to_base64(
        get_object_definition(Fruit, strict=True),
        "1",
    )
    assert value == "RnJ1aXQ6MQ=="


@pytest.mark.parametrize("value", [None, 1, 1.1, object()])
def test_to_base64_with_invalid_type(value: Any):
    with pytest.raises(ValueError):
        value = to_base64(value, "1")

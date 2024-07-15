from __future__ import annotations

import sys
from typing import Any
from unittest import mock

import pytest

from strawberry.relay.types import PREFIX
from strawberry.relay.utils import (
    SliceMetadata,
    from_base64,
    to_base64,
)
from strawberry.schema.config import StrawberryConfig
from strawberry.types.base import get_object_definition

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


@pytest.mark.parametrize(
    (
        "before",
        "after",
        "first",
        "last",
        "max_results",
        "expected",
        "expected_overfetch",
    ),
    [
        (
            None,
            None,
            None,
            None,
            100,
            SliceMetadata(start=0, end=100, expected=100),
            101,
        ),
        (
            None,
            None,
            None,
            None,
            200,
            SliceMetadata(start=0, end=200, expected=200),
            201,
        ),
        (
            None,
            None,
            10,
            None,
            100,
            SliceMetadata(start=0, end=10, expected=10),
            11,
        ),
        (
            None,
            None,
            None,
            10,
            100,
            SliceMetadata(start=0, end=sys.maxsize, expected=None),
            sys.maxsize,
        ),
        (
            10,
            None,
            None,
            None,
            100,
            SliceMetadata(start=0, end=10, expected=10),
            11,
        ),
        (
            None,
            10,
            None,
            None,
            100,
            SliceMetadata(start=11, end=111, expected=100),
            112,
        ),
        (
            15,
            None,
            10,
            None,
            100,
            SliceMetadata(start=14, end=24, expected=10),
            25,
        ),
        (
            None,
            15,
            None,
            10,
            100,
            SliceMetadata(start=16, end=sys.maxsize, expected=None),
            sys.maxsize,
        ),
    ],
)
def test_get_slice_metadata(
    before: str | None,
    after: str | None,
    first: int | None,
    last: int | None,
    max_results: int,
    expected: SliceMetadata,
    expected_overfetch: int,
):
    info = mock.Mock()
    info.schema.config = StrawberryConfig(relay_max_results=max_results)
    slice_metadata = SliceMetadata.from_arguments(
        info,
        before=before and to_base64(PREFIX, before),
        after=after and to_base64(PREFIX, after),
        first=first,
        last=last,
    )
    assert slice_metadata == expected
    assert slice_metadata.overfetch == expected_overfetch

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
        _type_name, _node_id = from_base64(value)


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
        _type_name, _node_id = from_base64(value)


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
            SliceMetadata(start=0, end=10, expected=10),
            11,
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


@pytest.mark.parametrize(
    ("before", "after", "first", "expected"),
    [
        # `before=15, first=10`: the Relay spec's reference algorithm applies
        # `before` first (keep edges strictly before it, i.e. positions 0..14),
        # then `first` takes the first N of *that* filtered slice. The result
        # must stay anchored at 0, not jump forward to just before `before`.
        (15, None, 10, SliceMetadata(start=0, end=10, expected=10)),
        # Fewer edges exist before the cursor than `first` asks for: the
        # window is bounded by `before`, not padded out to `first` items.
        (5, None, 10, SliceMetadata(start=0, end=5, expected=5)),
        # `after` establishes the true start; `before` bounds the end; `first`
        # must only shrink that window from the end, never move `start`.
        (20, 5, 3, SliceMetadata(start=6, end=9, expected=3)),
    ],
)
def test_get_slice_metadata_first_with_before(
    before: int,
    after: int | None,
    first: int,
    expected: SliceMetadata,
):
    """Regression test: `first` combined with `before` must paginate forward
    from the existing `start` (0, or wherever `after` put it), capping `end`
    at `start + first` -- not discard `start` and walk backward from `before`.
    """
    info = mock.Mock()
    info.schema.config = StrawberryConfig(relay_max_results=100)
    slice_metadata = SliceMetadata.from_arguments(
        info,
        before=to_base64(PREFIX, before),
        after=after and to_base64(PREFIX, after),
        first=first,
        last=None,
    )
    assert slice_metadata == expected

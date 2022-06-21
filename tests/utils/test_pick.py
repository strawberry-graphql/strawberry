import pytest

from strawberry.utils.pick import pick_not_none


def test_pick_first():
    assert pick_not_none(1, 2, 3) == 1


def test_pick_second():
    assert pick_not_none(None, 2, 3) == 2


def test_pick_third():
    assert pick_not_none(None, None, 3) == 3


def test_pick_none():
    with pytest.raises(ValueError):
        pick_not_none(None, None, None)


def test_pick_empty():
    with pytest.raises(ValueError):
        pick_not_none()

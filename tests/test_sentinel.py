import copy
import pickle

from strawberry.sentinel import sentinel


sent1 = sentinel("sent1")
sent2 = sentinel("sent2", repr="test_sentinels.sent2")


def test_identity():
    assert sent1 is sent1
    assert sent1 == sent1


def test_uniqueness():
    assert sent1 is not sent2
    assert sent1 != sent2
    assert sent1 is not None
    assert sent1 != None  # noqa: E711
    assert sent1 is not Ellipsis
    assert sent1 != Ellipsis  # noqa: E711
    assert sent1 is not "sent1"  # noqa: F632
    assert sent1 != "sent1"
    assert sent1 is not "<sent1>"  # noqa: F632
    assert sent1 != "<sent1>"


def test_reuse():
    sent1_other = sentinel("sent1")
    assert sent1 is sent1_other


def test_repr():
    assert repr(sent1) == "<sent1>"
    assert repr(sent2) == "test_sentinels.sent2"


def test_type():
    assert isinstance(sent1, type(sent1))
    assert isinstance(sent2, type(sent2))
    assert type(sent1) is not type(sent2)


def test_copy():
    assert sent1 is copy.copy(sent1)
    assert sent1 is copy.deepcopy(sent1)


def test_pickle_roundtrip():
    assert sent1 is pickle.loads(pickle.dumps(sent1))

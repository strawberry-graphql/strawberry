import typing
from typing import ClassVar, ForwardRef, Optional, Union

from strawberry.utils.typing import eval_type, get_optional_annotation, is_classvar


def test_get_optional_annotation():
    # Pair Union
    assert get_optional_annotation(Optional[Union[str, bool]]) == Union[str, bool]

    # More than pair Union
    assert (
        get_optional_annotation(Optional[Union[str, int, bool]])
        == Union[str, int, bool]
    )


def test_eval_type():
    class Foo:
        ...

    assert eval_type(ForwardRef("str")) is str
    assert eval_type(str) is str
    assert eval_type(ForwardRef("Foo"), None, locals()) is Foo
    assert eval_type(Foo, None, locals()) is Foo
    assert eval_type(ForwardRef("Optional[Foo]"), globals(), locals()) == Optional[Foo]
    assert eval_type(Optional["Foo"], globals(), locals()) == Optional[Foo]
    assert (
        eval_type(ForwardRef("Union[Foo, str]"), globals(), locals()) == Union[Foo, str]
    )
    assert eval_type(Union["Foo", "str"], globals(), locals()) == Union[Foo, str]
    assert (
        eval_type(ForwardRef("Optional[Union[Foo, str]]"), globals(), locals())
        == Union[Foo, str, None]
    )


def test_is_classvar():
    class Foo:
        attr1: str
        attr2: ClassVar[str]
        attr3: typing.ClassVar[str]

    assert not is_classvar(Foo, Foo.__annotations__["attr1"])
    assert is_classvar(Foo, Foo.__annotations__["attr2"])
    assert is_classvar(Foo, Foo.__annotations__["attr3"])

from typing import ForwardRef, Optional, Union

from strawberry.utils.typing import eval_type, get_optional_annotation


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

from __future__ import annotations

import typing
from typing import ClassVar, ForwardRef, Optional, Union

from strawberry.scalars import JSON
from strawberry.utils.typing import eval_type, is_classvar


def test_eval_type():
    class Foo: ...

    assert eval_type(ForwardRef("Foo | None"), globals(), locals()) == Optional[Foo]
    assert eval_type(ForwardRef("Foo | str"), globals(), locals()) == Union[Foo, str]
    assert (
        eval_type(ForwardRef("Foo | str | None"), globals(), locals())
        == Union[Foo, str, None]
    )
    assert (
        eval_type(ForwardRef("list[Foo | str] | None"), globals(), locals())
        == Union[list[Union[Foo, str]], None]
    )
    assert (
        eval_type(ForwardRef("list[Foo | str] | None | int"), globals(), locals())
        == Union[list[Union[Foo, str]], int, None]
    )
    assert eval_type(ForwardRef("JSON | None"), globals(), locals()) == Optional[JSON]


def test_eval_type_generic_type_alias():
    class Foo: ...

    assert eval_type(ForwardRef("Foo | None"), globals(), locals()) == Optional[Foo]
    assert eval_type(ForwardRef("Foo | str"), globals(), locals()) == Union[Foo, str]
    assert (
        eval_type(ForwardRef("Foo | str | None"), globals(), locals())
        == Union[Foo, str, None]
    )
    assert (
        eval_type(ForwardRef("list[Foo | str] | None"), globals(), locals())
        == Union[list[Union[Foo, str]], None]  # type: ignore
    )
    assert (
        eval_type(ForwardRef("list[Foo | str] | None | int"), globals(), locals())
        == Union[list[Union[Foo, str]], int, None]  # type: ignore
    )


def test_is_classvar():
    class Foo:
        attr1: str
        attr2: ClassVar[str]
        attr3: typing.ClassVar[str]

    assert not is_classvar(Foo, Foo.__annotations__["attr1"])
    assert is_classvar(Foo, Foo.__annotations__["attr2"])
    assert is_classvar(Foo, Foo.__annotations__["attr3"])

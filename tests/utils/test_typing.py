import typing
from typing import Annotated, ClassVar, ForwardRef, Optional, Union

import strawberry
from strawberry.types.lazy_type import LazyType
from strawberry.utils.typing import eval_type, get_optional_annotation, is_classvar


@strawberry.type
class Fruit: ...


def test_get_optional_annotation():
    # Pair Union
    assert get_optional_annotation(Optional[Union[str, bool]]) == Union[str, bool]

    # More than pair Union
    assert (
        get_optional_annotation(Optional[Union[str, int, bool]])
        == Union[str, int, bool]
    )


def test_eval_type():
    class Foo: ...

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
    assert (
        eval_type(ForwardRef("Annotated[str, 'foobar']"), globals(), locals())
        is Annotated[str, "foobar"]
    )
    assert (
        eval_type(
            ForwardRef("Annotated[Fruit, strawberry.lazy('tests.utils.test_typing')]"),
            {"strawberry": strawberry, "Annotated": Annotated},
            None,
        )
        == Annotated[
            LazyType("Fruit", "tests.utils.test_typing"),
            strawberry.lazy("tests.utils.test_typing"),
        ]
    )
    assert (
        eval_type(
            ForwardRef("Annotated[strawberry.auto, 'foobar']"),
            {"strawberry": strawberry, "Annotated": Annotated},
            None,
        )
        == Annotated[strawberry.auto, "foobar"]
    )
    assert (
        eval_type(
            ForwardRef("Annotated[datetime, strawberry.lazy('datetime')]"),
            {"strawberry": strawberry, "Annotated": Annotated},
            None,
        )
        == Annotated[
            LazyType("datetime", "datetime"),
            strawberry.lazy("datetime"),
        ]
    )


def test_eval_type_with_deferred_annotations():
    assert (
        eval_type(
            ForwardRef(
                "Annotated['Fruit', strawberry.lazy('tests.utils.test_typing')]"
            ),
            {"strawberry": strawberry, "Annotated": Annotated},
            None,
        )
        == Annotated[
            LazyType("Fruit", "tests.utils.test_typing"),
            strawberry.lazy("tests.utils.test_typing"),
        ]
    )
    assert (
        eval_type(
            ForwardRef("Annotated['datetime', strawberry.lazy('datetime')]"),
            {"strawberry": strawberry, "Annotated": Annotated},
            None,
        )
        == Annotated[
            LazyType("datetime", "datetime"),
            strawberry.lazy("datetime"),
        ]
    )


def test_is_classvar():
    class Foo:
        attr1: str
        attr2: ClassVar[str]
        attr3: typing.ClassVar[str]

    assert not is_classvar(Foo, Foo.__annotations__["attr1"])
    assert is_classvar(Foo, Foo.__annotations__["attr2"])
    assert is_classvar(Foo, Foo.__annotations__["attr3"])

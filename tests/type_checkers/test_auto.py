from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
import strawberry


@strawberry.type
class SomeType:
    foobar: strawberry.auto


obj1 = SomeType(foobar=1)
obj2 = SomeType(foobar="some text")
obj3 = SomeType(foobar={"some key": "some value"})

reveal_type(obj1.foobar)
reveal_type(obj2.foobar)
reveal_type(obj3.foobar)
"""


def test_auto():
    result = typecheck(CODE)

    assert result.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "obj1.foobar" is "Any"',
                line=14,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "obj2.foobar" is "Any"',
                line=15,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "obj3.foobar" is "Any"',
                line=16,
                column=13,
            ),
        ]
    )

    assert result.mypy == snapshot(
        [
            Result(type="note", message='Revealed type is "Any"', line=14, column=13),
            Result(type="note", message='Revealed type is "Any"', line=15, column=13),
            Result(type="note", message='Revealed type is "Any"', line=16, column=13),
        ]
    )

from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]

CODE = """
import strawberry
from strawberry.types.base import StrawberryOptional, StrawberryList


@strawberry.type
class Fruit:
    name: str


reveal_type(StrawberryOptional(Fruit))
reveal_type(StrawberryList(Fruit))
reveal_type(StrawberryOptional(StrawberryList(Fruit)))
reveal_type(StrawberryList(StrawberryOptional(Fruit)))

reveal_type(StrawberryOptional(str))
reveal_type(StrawberryList(str))
reveal_type(StrawberryOptional(StrawberryList(str)))
reveal_type(StrawberryList(StrawberryOptional(str)))
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "StrawberryOptional(Fruit)" is "StrawberryOptional"',
                line=11,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "StrawberryList(Fruit)" is "StrawberryList"',
                line=12,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "StrawberryOptional(StrawberryList(Fruit))" is "StrawberryOptional"',
                line=13,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "StrawberryList(StrawberryOptional(Fruit))" is "StrawberryList"',
                line=14,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "StrawberryOptional(str)" is "StrawberryOptional"',
                line=16,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "StrawberryList(str)" is "StrawberryList"',
                line=17,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "StrawberryOptional(StrawberryList(str))" is "StrawberryOptional"',
                line=18,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "StrawberryList(StrawberryOptional(str))" is "StrawberryList"',
                line=19,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "strawberry.types.base.StrawberryOptional"',
                line=11,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.types.base.StrawberryList"',
                line=12,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.types.base.StrawberryOptional"',
                line=13,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.types.base.StrawberryList"',
                line=14,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.types.base.StrawberryOptional"',
                line=16,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.types.base.StrawberryList"',
                line=17,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.types.base.StrawberryOptional"',
                line=18,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "strawberry.types.base.StrawberryList"',
                line=19,
                column=13,
            ),
        ]
    )

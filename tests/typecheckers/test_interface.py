from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
import strawberry


@strawberry.interface
class Node:
    id: strawberry.ID

reveal_type(Node)
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "Node" is "type[Node]"',
                line=9,
                column=13,
            )
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "def (*, id: strawberry.scalars.ID) -> mypy_test.Node"',
                line=9,
                column=13,
            )
        ]
    )


CODE_2 = """
import strawberry


@strawberry.interface(name="nodeinterface")
class Node:
    id: strawberry.ID

reveal_type(Node)
"""


def test_calling():
    results = typecheck(CODE_2)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "Node" is "type[Node]"',
                line=9,
                column=13,
            )
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "def (*, id: strawberry.scalars.ID) -> mypy_test.Node"',
                line=9,
                column=13,
            )
        ]
    )

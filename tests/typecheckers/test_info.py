from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


def test_with_params():
    CODE = """
import strawberry

def example(info: strawberry.Info[None, None]) -> None:
    reveal_type(info.context)
    reveal_type(info.root_value)
"""

    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "info.context" is "None"',
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message='Type of "info.root_value" is "None"',
                line=6,
                column=17,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(type="note", message='Revealed type is "None"', line=5, column=17),
            Result(type="note", message='Revealed type is "None"', line=6, column=17),
        ]
    )


def test_with_one_param():
    CODE = """
import strawberry

def example(info: strawberry.Info[None]) -> None:
    reveal_type(info.context)
    reveal_type(info.root_value)
"""

    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "info.context" is "None"',
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message='Type of "info.root_value" is "Any"',
                line=6,
                column=17,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(type="note", message='Revealed type is "None"', line=5, column=17),
            Result(type="note", message='Revealed type is "Any"', line=6, column=17),
        ]
    )


def test_without_params():
    CODE = """
import strawberry

def example(info: strawberry.Info) -> None:
    reveal_type(info.context)
    reveal_type(info.root_value)
"""

    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "info.context" is "Any"',
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message='Type of "info.root_value" is "Any"',
                line=6,
                column=17,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(type="note", message='Revealed type is "Any"', line=5, column=17),
            Result(type="note", message='Revealed type is "Any"', line=6, column=17),
        ]
    )

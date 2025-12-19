from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]


CODE = """
import strawberry


@strawberry.type
class User:
    name: str


User("Patrick")

reveal_type(User.__init__)
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message="Expected 0 positional arguments",
                line=10,
                column=6,
            ),
            Result(
                type="information",
                message='Type of "User.__init__" is "(self: User, *, name: str) -> None"',
                line=12,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Too many positional arguments for "User"',
                line=10,
                column=1,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, name: builtins.str)"',
                line=12,
                column=13,
            ),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="error",
                message="No argument provided for required parameter `name`",
                line=10,
                column=1,
            ),
            Result(
                type="error",
                message="Too many positional arguments: expected 0, got 1",
                line=10,
                column=6,
            ),
            Result(
                type="information",
                message="Revealed type: `(self: User, *, name: str) -> None`",
                line=12,
                column=13,
            ),
        ]
    )

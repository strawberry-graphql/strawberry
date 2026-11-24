from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]


CODE = """
from dataclasses import dataclass

import strawberry


@dataclass
class MyContext:
    user_id: str


@strawberry.type
class Query:
    @strawberry.field
    def user_id(self, context: strawberry.Context[MyContext]) -> str:
        reveal_type(context)
        return context.user_id
"""


def test_context():
    result = typecheck(CODE)

    assert result.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "context" is "MyContext"',
                line=16,
                column=21,
            )
        ]
    )
    assert result.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "mypy_test.MyContext"',
                line=16,
                column=21,
            )
        ]
    )
    assert result.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `MyContext`",
                line=16,
                column=21,
            )
        ]
    )

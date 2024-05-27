from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
import strawberry


@strawberry.type
class User:
    name: str
    age: strawberry.Private[int]


patrick = User(name="Patrick", age=1)
User(n="Patrick")

reveal_type(patrick.name)
reveal_type(patrick.age)
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message='Arguments missing for parameters "name", "age"',
                line=12,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=12, column=6),
            Result(
                type="information",
                message='Type of "patrick.name" is "str"',
                line=14,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "patrick.age" is "int"',
                line=15,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "User"',
                line=12,
                column=1,
            ),
            Result(
                type="note",
                message='Revealed type is "builtins.str"',
                line=14,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "builtins.int"',
                line=15,
                column=13,
            ),
        ]
    )

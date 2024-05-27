from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]

CODE = """
import strawberry


@strawberry.type(name="User")
class UserModel:
    name: str


@strawberry.input(name="User")
class UserInput:
    name: str


UserModel(name="Patrick")
UserModel(n="Patrick")

UserInput(name="Patrick")
UserInput(n="Patrick")
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message='Argument missing for parameter "name"',
                line=16,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=16, column=11),
            Result(
                type="error",
                message='Argument missing for parameter "name"',
                line=19,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=19, column=11),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "UserModel"',
                line=16,
                column=1,
            ),
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "UserInput"',
                line=19,
                column=1,
            ),
        ]
    )

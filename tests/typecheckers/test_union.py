from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
import strawberry
from typing_extensions import TypeAlias, Annotated
from typing import Union

@strawberry.type
class User:
    name: str


@strawberry.type
class Error:
    message: str

UserOrError: TypeAlias = Annotated[
    Union[User, Error],  strawberry.union("UserOrError")
]

reveal_type(UserOrError)

x: UserOrError = User(name="Patrick")

reveal_type(x)
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "UserOrError" is "Annotated"',
                line=19,
                column=13,
            ),
            Result(
                type="information", message='Type of "x" is "User"', line=23, column=13
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "typing._SpecialForm"',
                line=19,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "Union[mypy_test.User, mypy_test.Error]"',
                line=23,
                column=13,
            ),
        ]
    )

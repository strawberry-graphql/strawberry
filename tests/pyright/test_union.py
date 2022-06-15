from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]


CODE = """
import strawberry
from typing_extensions import TypeAlias

@strawberry.type
class User:
    name: str


@strawberry.type
class Error:
    message: str

UserOrError: TypeAlias = strawberry.union("UserOrError", (User, Error))

reveal_type(UserOrError)

x: UserOrError = User(name="Patrick")

reveal_type(x)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="information",
            message='Type of "UserOrError" is "Type[User] | Type[Error]"',
            line=16,
            column=13,
        ),
        Result(type="information", message='Type of "x" is "User"', line=20, column=13),
    ]

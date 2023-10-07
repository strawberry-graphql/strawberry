from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


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


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="information",
            message='Type of "UserOrError" is "type[User] | type[Error]"',
            line=19,
            column=13,
        ),
        Result(type="information", message='Type of "x" is "User"', line=23, column=13),
    ], f"Actual results:\n{results}"

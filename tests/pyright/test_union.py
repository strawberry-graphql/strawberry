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

UserOrError: TypeAlias = strawberry.union("UserOrError", (User, Error))  # type: ignore

reveal_type(UserOrError)

x: UserOrError = User(name="Patrick")

reveal_type(x)
"""


# Pyright removed support for being able to return a type from a function
# in future we'll probably implement union using Annotated so we can
# get a more type friendly API :)


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="information",
            message='Type of "UserOrError" is "Unknown"',
            line=16,
            column=13,
        ),
        Result(
            type="error",
            message='Type of "x" is unknown (reportUnknownVariableType)',
            line=18,
            column=1,
        ),
        Result(
            type="information", message='Type of "x" is "Unknown"', line=20, column=13
        ),
    ]

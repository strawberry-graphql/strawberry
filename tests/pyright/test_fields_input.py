from .utils import Result, run_pyright


CODE = """
import strawberry


@strawberry.input
class User:
    name: str


User(name="Patrick")
User(n="Patrick")

reveal_type(User)
reveal_type(User.__init__)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=11,
            column=6,
        ),
        Result(
            type="error",
            message='Argument missing for parameter "name" (reportGeneralTypeIssues)',
            line=11,
            column=1,
        ),
        Result(
            type="info", message='Type of "User" is "Type[User]"', line=13, column=13
        ),
        Result(
            type="info",
            message='Type of "User.__init__" is "(self: User, name: str) -> None"',
            line=14,
            column=13,
        ),
    ]

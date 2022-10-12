from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]


CODE = """
import strawberry


@strawberry.type
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
            type="information",
            message='Type of "User" is "Type[User]"',
            line=13,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "User.__init__" is "(self: User, *, name: str) -> None"',
            line=14,
            column=13,
        ),
    ]

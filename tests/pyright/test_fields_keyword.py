from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]


CODE = """
import strawberry


@strawberry.type
class User:
    name: str


User("Patrick")

reveal_type(User.__init__)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message="Expected 0 positional arguments (reportGeneralTypeIssues)",
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

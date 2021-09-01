import pytest

from .utils import Result, pyright_exist, run_pyright


pytestmark = pytest.mark.skipif(
    not pyright_exist(), reason="These tests require pyright"
)
CODE = """
import strawberry

def get_user_age() -> int:
    return 0


@strawberry.input
class User:
    name: str
    # pyright needs `init=False` do remove this field from the signature
    # we keep this test to make this is an expected behavior
    age: int = strawberry.field(resolver=get_user_age)


User(name="Patrick")

reveal_type(User)
reveal_type(User.__init__)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message='Argument missing for parameter "age" (reportGeneralTypeIssues)',
            line=16,
            column=1,
        ),
        Result(
            type="info", message='Type of "User" is "Type[User]"', line=18, column=13
        ),
        Result(
            type="info",
            message=(
                'Type of "User.__init__" is '
                '"(self: User, name: str, age: int) -> None"'
            ),
            line=19,
            column=13,
        ),
    ]

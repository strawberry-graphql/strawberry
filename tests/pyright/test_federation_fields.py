from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]

CODE = """
import strawberry


@strawberry.federation.type
class User:
    age: int = strawberry.federation.field(description="Age")
    name: str

@strawberry.federation.input
class UserInput:
    age: int = strawberry.federation.field(description="Age")
    name: str


User(name="Patrick", age=1)
User(n="Patrick", age=1)

UserInput(name="Patrick", age=1)
UserInput(n="Patrick", age=1)

reveal_type(User)
reveal_type(User.__init__)

reveal_type(UserInput)
reveal_type(UserInput.__init__)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=17,
            column=6,
        ),
        Result(
            type="error",
            message='Argument missing for parameter "name" (reportGeneralTypeIssues)',
            line=17,
            column=1,
        ),
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=20,
            column=11,
        ),
        Result(
            type="error",
            message='Argument missing for parameter "name" '
            "(reportGeneralTypeIssues)",
            line=20,
            column=1,
        ),
        Result(
            type="information",
            message='Type of "User" is "Type[User]"',
            line=22,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "User.__init__" is "(self: User, *, age: int, name: str) '
            '-> None"',
            line=23,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "UserInput" is "Type[UserInput]"',
            line=25,
            column=13,
        ),
        Result(
            type="information",
            message=(
                'Type of "UserInput.__init__" is "(self: UserInput, *, age: int, '
                'name: str) -> None"'
            ),
            line=26,
            column=13,
        ),
    ]

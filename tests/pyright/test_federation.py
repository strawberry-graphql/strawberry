from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]


CODE = """
import strawberry

def get_user_age() -> int:
    return 0


@strawberry.federation.type
class User:
    name: str
    age: int = strawberry.field(resolver=get_user_age)
    something_else: int = strawberry.federation.field(resolver=get_user_age)


User(name="Patrick")
User(n="Patrick")

reveal_type(User)
reveal_type(User.__init__)
"""


def test_federation_type():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=16,
            column=6,
        ),
        Result(
            type="error",
            message='Argument missing for parameter "name" (reportGeneralTypeIssues)',
            line=16,
            column=1,
        ),
        Result(
            type="information",
            message='Type of "User" is "Type[User]"',
            line=18,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "User.__init__" is "(self: User, *, name: str) -> None"',
            line=19,
            column=13,
        ),
    ]


CODE_INTERFACE = """
import strawberry


@strawberry.federation.interface
class User:
    name: str
    age: int


User(name="Patrick", age=1)
User(n="Patrick", age=1)

reveal_type(User)
reveal_type(User.__init__)
"""


def test_federation_interface():
    results = run_pyright(CODE_INTERFACE)

    assert results == [
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=12,
            column=6,
        ),
        Result(
            type="error",
            message='Argument missing for parameter "name" (reportGeneralTypeIssues)',
            line=12,
            column=1,
        ),
        Result(
            type="information",
            message='Type of "User" is "Type[User]"',
            line=14,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "User.__init__" is "(self: User, *, name: str, age: int) -> None"',
            line=15,
            column=13,
        ),
    ]


CODE_INPUT = """
import strawberry

@strawberry.federation.input
class User:
    name: str


User(name="Patrick")
User(n="Patrick")

reveal_type(User)
reveal_type(User.__init__)
"""


def test_federation_input():
    results = run_pyright(CODE_INPUT)

    assert results == [
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=10,
            column=6,
        ),
        Result(
            type="error",
            message='Argument missing for parameter "name" (reportGeneralTypeIssues)',
            line=10,
            column=1,
        ),
        Result(
            type="information",
            message='Type of "User" is "Type[User]"',
            line=12,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "User.__init__" is "(self: User, *, name: str) -> None"',
            line=13,
            column=13,
        ),
    ]

from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]

CODE = """
import strawberry

def some_resolver(root: "User") -> str:
    return "An address"

def some_resolver_2() -> str:
    return "Another address"

@strawberry.federation.type
class User:
    age: int = strawberry.federation.field(description="Age")
    name: str
    address: str = strawberry.federation.field(resolver=some_resolver)
    another_address: str = strawberry.federation.field(resolver=some_resolver_2)

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


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message='Argument missing for parameter "name"',
                line=24,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=24, column=6),
            Result(
                type="error",
                message='Argument missing for parameter "name"',
                line=27,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=27, column=11),
            Result(
                type="information",
                message='Type of "User" is "type[User]"',
                line=29,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "User.__init__" is "(self: User, *, age: int, name: str) -> None"',
                line=30,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "UserInput" is "type[UserInput]"',
                line=32,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "UserInput.__init__" is "(self: UserInput, *, age: int, name: str) -> None"',
                line=33,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "User"',
                line=24,
                column=1,
            ),
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "UserInput"',
                line=27,
                column=1,
            ),
            Result(
                type="note",
                message='Revealed type is "def (*, age: builtins.int, name: builtins.str) -> mypy_test.User"',
                line=29,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, age: builtins.int, name: builtins.str)"',
                line=30,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (*, age: builtins.int, name: builtins.str) -> mypy_test.UserInput"',
                line=32,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.UserInput, *, age: builtins.int, name: builtins.str)"',
                line=33,
                column=13,
            ),
        ]
    )

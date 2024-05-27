from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


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
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message='Argument missing for parameter "name"',
                line=16,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=16, column=6),
            Result(
                type="information",
                message='Type of "User" is "type[User]"',
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
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "User"',
                line=16,
                column=1,
            ),
            Result(
                type="note",
                message='Revealed type is "def (*, name: builtins.str) -> mypy_test.User"',
                line=18,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, name: builtins.str)"',
                line=19,
                column=13,
            ),
        ]
    )


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
    results = typecheck(CODE_INTERFACE)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message='Argument missing for parameter "name"',
                line=12,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=12, column=6),
            Result(
                type="information",
                message='Type of "User" is "type[User]"',
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
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "User"',
                line=12,
                column=1,
            ),
            Result(
                type="note",
                message='Revealed type is "def (*, name: builtins.str, age: builtins.int) -> mypy_test.User"',
                line=14,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, name: builtins.str, age: builtins.int)"',
                line=15,
                column=13,
            ),
        ]
    )


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
    results = typecheck(CODE_INPUT)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message='Argument missing for parameter "name"',
                line=10,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=10, column=6),
            Result(
                type="information",
                message='Type of "User" is "type[User]"',
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
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "User"',
                line=10,
                column=1,
            ),
            Result(
                type="note",
                message='Revealed type is "def (*, name: builtins.str) -> mypy_test.User"',
                line=12,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, name: builtins.str)"',
                line=13,
                column=13,
            ),
        ]
    )

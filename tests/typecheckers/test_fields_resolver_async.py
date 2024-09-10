from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]

CODE = """
import strawberry

async def get_user_age() -> int:
    return 0


@strawberry.type
class User:
    name: str
    age: int = strawberry.field(resolver=get_user_age)
    something: str = strawberry.field(resolver=get_user_age)


User(name="Patrick")
User(n="Patrick")

reveal_type(User)
reveal_type(User.__init__)
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message=(
                    'Type "int" is not assignable to declared type "str"\n'
                    '\xa0\xa0"int" is not assignable to "str"'
                ),
                line=12,
                column=22,
            ),
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
                message='Incompatible types in assignment (expression has type "int", variable has type "str")',
                line=12,
                column=22,
            ),
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

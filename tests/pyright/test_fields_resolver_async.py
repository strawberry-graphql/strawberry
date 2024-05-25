from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]

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


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message=(
                'Expression of type "StrawberryField" is incompatible with '
                'declared type "str"\n'
                '\xa0\xa0"StrawberryField" is incompatible with "str"'
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
        Result(
            type="error",
            message='No parameter named "n"',
            line=16,
            column=6,
        ),
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

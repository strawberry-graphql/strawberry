from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]

CODE = """
import strawberry

def get_user_age() -> int:
    return 0


@strawberry.type
class User:
    name: str
    age: strawberry.Resolver[int] = strawberry.field(resolver=get_user_age)


User(name="Patrick")
User(n="Patrick")

reveal_type(User)
reveal_type(User.__init__)

def test_reading(user: User) -> int:
    return user.age

def test_writing(user: User, value: int) -> None:
    user.age = value

def test_cant_instantiate_resolver() -> strawberry.Resolver[int]:
    return strawberry.Resolver()
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message='Argument missing for parameter "name"',
            line=15,
            column=1,
        ),
        Result(
            type="error",
            message='No parameter named "n"',
            line=15,
            column=6,
        ),
        Result(
            type="information",
            message='Type of "User" is "type[User]"',
            line=17,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "User.__init__" is "(self: User, *, name: str) -> None"',
            line=18,
            column=13,
        ),
        Result(
            type="error",
            message=(
                'Expression of type "Resolver[int]" cannot be assigned to return type "int"'
                '\n\xa0\xa0"Resolver[int]" is incompatible with "int"'
            ),
            line=21,
            column=12,
        ),
        Result(
            type="error",
            message=(
                'Cannot assign member "age" for type "User"'
                '\n\xa0\xa0"int" is incompatible with "Resolver[int]"'
            ),
            line=24,
            column=16,
        ),
        Result(
            type="error",
            message=(
                'Cannot instantiate abstract class "Resolver"'
                '\n\xa0\xa0"Resolver.__do_not_instantiate_this" is not implemented'
            ),
            line=27,
            column=12,
        ),
    ]

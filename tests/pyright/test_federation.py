from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


CODE = """
import strawberry

def get_user_age() -> int:
    return 0


@strawberry.federation.type
class User:
    name: str
    age: strawberry.Resolver[int] = strawberry.federation.field(resolver=get_user_age)
    something_else: strawberry.Resolver[int] = strawberry.federation.field(resolver=get_user_age)


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


def test_federation_type():
    results = run_pyright(CODE)

    assert results == [
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
        Result(
            type="error",
            message=(
                'Expression of type "Resolver[int]" cannot be assigned to return type "int"'
                '\n\xa0\xa0"Resolver[int]" is incompatible with "int"'
            ),
            line=22,
            column=12,
        ),
        Result(
            type="error",
            message=(
                'Cannot assign member "age" for type "User"'
                '\n\xa0\xa0"int" is incompatible with "Resolver[int]"'
            ),
            line=25,
            column=16,
        ),
        Result(
            type="error",
            message=(
                'Cannot instantiate abstract class "Resolver"'
                '\n\xa0\xa0"Resolver.__do_not_instantiate_this" is not implemented'
            ),
            line=28,
            column=12,
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
            message='Argument missing for parameter "name"',
            line=12,
            column=1,
        ),
        Result(
            type="error",
            message='No parameter named "n"',
            line=12,
            column=6,
        ),
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
            message='Argument missing for parameter "name"',
            line=10,
            column=1,
        ),
        Result(
            type="error",
            message='No parameter named "n"',
            line=10,
            column=6,
        ),
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

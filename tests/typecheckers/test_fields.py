from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
import strawberry


@strawberry.type
class User:
    name: str


User(name="Patrick")
User(n="Patrick")

reveal_type(User)
reveal_type(User.__init__)

def some_resolver() -> str:
    return ""

@strawberry.type
class Example:
    a: strawberry.Resolver[str] = strawberry.field(resolver=some_resolver)

def test_reading(example: Example) -> str:
    return example.a

def test_writing(example: Example, value: str) -> None:
    example.a = value

def test_cant_instantiate_resolver() -> strawberry.Resolver[str]:
    return strawberry.Resolver()
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="error",
                message='Argument missing for parameter "name"',
                line=11,
                column=1,
            ),
            Result(type="error", message='No parameter named "n"', line=11, column=6),
            Result(
                type="information",
                message='Type of "User" is "type[User]"',
                line=13,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "User.__init__" is "(self: User, *, name: str) -> None"',
                line=14,
                column=13,
            ),
            Result(
                type="error",
                message="""\
Expression of type "Resolver[str]" is incompatible with return type "str"
\xa0\xa0"Resolver[str]" is incompatible with "str"\
""",
                line=24,
                column=12,
            ),
            Result(
                type="error",
                message="""\
Cannot assign to attribute "a" for class "Example"
\xa0\xa0"str" is incompatible with "Resolver[str]"\
""",
                line=27,
                column=17,
            ),
            Result(
                type="error",
                message="""\
Cannot instantiate abstract class "Resolver"
\xa0\xa0"Resolver.__do_not_instantiate_this" is not implemented\
""",
                line=30,
                column=12,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "User"',
                line=11,
                column=1,
            ),
            Result(
                type="note",
                message='Revealed type is "def (*, name: builtins.str) -> mypy_test.User"',
                line=13,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, name: builtins.str)"',
                line=14,
                column=13,
            ),
            Result(
                type="error",
                message='Incompatible return value type (got "Resolver[str]", expected "str")',
                line=24,
                column=12,
            ),
            Result(
                type="error",
                message='Incompatible types in assignment (expression has type "str", variable has type "Resolver[str]")',
                line=27,
                column=17,
            ),
            Result(
                type="error",
                message='Cannot instantiate abstract class "Resolver" with abstract attribute "__do_not_instantiate_this"',
                line=30,
                column=12,
            ),
        ]
    )

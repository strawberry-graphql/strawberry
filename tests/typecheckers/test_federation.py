from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]


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
                message='Revealed type is "def (*, name: str) -> mypy_test.User"',
                line=18,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, name: str)"',
                line=19,
                column=13,
            ),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="error",
                message="No argument provided for required parameter `name`",
                line=16,
                column=1,
            ),
            Result(
                type="error",
                message="Argument `n` does not match any known parameter",
                line=16,
                column=6,
            ),
            Result(
                type="information",
                message="Revealed type: `<class 'User'>`",
                line=18,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `(self: User, *, name: str) -> None`",
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
                message='Revealed type is "def (*, name: str, age: int) -> mypy_test.User"',
                line=14,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, name: str, age: int)"',
                line=15,
                column=13,
            ),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="error",
                message="No argument provided for required parameter `name`",
                line=12,
                column=1,
            ),
            Result(
                type="error",
                message="Argument `n` does not match any known parameter",
                line=12,
                column=6,
            ),
            Result(
                type="information",
                message="Revealed type: `<class 'User'>`",
                line=14,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `(self: User, *, name: str, age: int) -> None`",
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
                message='Revealed type is "def (*, name: str) -> mypy_test.User"',
                line=12,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "def (self: mypy_test.User, *, name: str)"',
                line=13,
                column=13,
            ),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="error",
                message="No argument provided for required parameter `name`",
                line=10,
                column=1,
            ),
            Result(
                type="error",
                message="Argument `n` does not match any known parameter",
                line=10,
                column=6,
            ),
            Result(
                type="information",
                message="Revealed type: `<class 'User'>`",
                line=12,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `(self: User, *, name: str) -> None`",
                line=13,
                column=13,
            ),
        ]
    )


CODE_SCALAR = """
import strawberry
from datetime import datetime
from graphql.language import ast

def parse_epoch_literal(
    node: ast.ValueNode, variables: dict[str, object] | None = None
) -> datetime:
    assert isinstance(node, ast.IntValueNode)
    return datetime.fromtimestamp(int(node.value))

EpochDateTime = strawberry.federation.scalar(
    datetime,
    name="EpochDateTime",
    serialize=lambda value: int(value.timestamp()),
    parse_value=lambda value: datetime.fromtimestamp(int(value)),
    parse_literal=parse_epoch_literal,
)

reveal_type(EpochDateTime)
"""


def test_federation_scalar():
    results = typecheck(CODE_SCALAR)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "EpochDateTime" is "type[datetime]"',
                line=20,
                column=13,
            )
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "def (year: typing.SupportsIndex, month: typing.SupportsIndex, day: typing.SupportsIndex, hour: typing.SupportsIndex =, minute: typing.SupportsIndex =, second: typing.SupportsIndex =, microsecond: typing.SupportsIndex =, tzinfo: datetime.tzinfo | None =, *, fold: int =) -> datetime.datetime"',
                line=20,
                column=13,
            )
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `<class 'datetime'>`",
                line=20,
                column=13,
            )
        ]
    )

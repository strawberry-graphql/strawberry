from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
import strawberry


@strawberry.type
class SomeType:
    foobar: strawberry.Maybe[str]


obj = SomeType(foobar="some text")

reveal_type(obj.foobar)

if strawberry.not_unset(obj.foobar):
    reveal_type(obj.foobar)
"""


def test_maybe() -> None:
    result = typecheck(CODE)
    
    assert result.pyright == snapshot([
    Result(
        type="information",
        message='Type of "obj.foobar" is "str | UnsetType | None"',
        line=12,
        column=13,
    ),
    Result(
        type="information",
        message='Type of "obj.foobar" is "str | None"',
        line=15,
        column=17,
    ),
])

    assert result.mypy == snapshot([
    Result(
        type="note",
        message='Revealed type is "Union[builtins.str, strawberry.types.unset.UnsetType, None]"',
        line=12,
        column=13,
    ),
    Result(
        type="note",
        message='Revealed type is "Union[builtins.str, None]"',
        line=15,
        column=17,
    ),
])
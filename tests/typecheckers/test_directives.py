from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
import strawberry
from strawberry.directive import DirectiveLocation

@strawberry.directive(
    locations=[DirectiveLocation.FRAGMENT_DEFINITION],
    description="description.",
)
def make_int(value: str) -> int:
    '''description.'''
    try:
        return int(value)
    except ValueError:
        return 0

reveal_type(make_int)
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "make_int" is "StrawberryDirective[int]"',
                line=16,
                column=13,
            )
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "strawberry.directive.StrawberryDirective[builtins.int]"',
                line=16,
                column=13,
            )
        ]
    )

from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


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


def test_pyright():
    results = run_pyright(CODE)
    assert results == [
        Result(
            type="information",
            message='Type of "make_int" is "StrawberryDirective[int]"',
            line=16,
            column=13,
        ),
    ]

from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]


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
                message='Revealed type is "strawberry.directive.StrawberryDirective[int]"',
                line=16,
                column=13,
            )
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `StrawberryDirective[int]`",
                line=16,
                column=13,
            ),
        ]
    )


def test_schema_directive_custom_ordering_method():
    code = """
from strawberry.schema_directive import Location, schema_directive


@schema_directive(locations=[Location.OBJECT])
class UserDirective:
    name: str

    def __gt__(self, other: "UserDirective") -> bool:
        return self.name > other.name


reveal_type(UserDirective)
"""

    results = typecheck(code)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "UserDirective" is "type[UserDirective]"',
                line=13,
                column=13,
            )
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "def (*, name: str) -> mypy_test.UserDirective"',
                line=13,
                column=13,
            )
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `<class 'UserDirective'>`",
                line=13,
                column=13,
            )
        ]
    )


def test_federation_schema_directive_custom_ordering_method():
    code = """
from strawberry.federation.schema_directive import schema_directive
from strawberry.schema_directive import Location


@schema_directive(locations=[Location.OBJECT])
class UserDirective:
    name: str

    def __gt__(self, other: "UserDirective") -> bool:
        return self.name > other.name


reveal_type(UserDirective)
"""

    results = typecheck(code)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "UserDirective" is "type[UserDirective]"',
                line=14,
                column=13,
            )
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "def (*, name: str) -> mypy_test.UserDirective"',
                line=14,
                column=13,
            )
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `<class 'UserDirective'>`",
                line=14,
                column=13,
            )
        ]
    )

from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]


CODE = """
from typing import TYPE_CHECKING
import strawberry
from strawberry.lazy_type import Lazy

if TYPE_CHECKING:
    from strawberry.scalars import JSON


@strawberry.type
class SomeType:
    json: Lazy["JSON", "strawberry.scalars"]


obj = SomeType(
    json=JSON({"foo": "bar"}),
)

reveal_type(SomeType.json)
reveal_type(obj.json)
"""


def test_pyright():
    results = run_pyright(CODE)
    assert results == [
        Result(
            type="information",
            message='Type of "SomeType.json" is "JSON"',
            line=19,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "obj.json" is "JSON"',
            line=20,
            column=13,
        ),
    ]

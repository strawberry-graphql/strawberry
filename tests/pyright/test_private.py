from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]


CODE = """
import strawberry


@strawberry.type
class User:
    name: str
    age: strawberry.Private[int]


patrick = User(name="Patrick", age=1)
User(n="Patrick")

reveal_type(patrick.name)
reveal_type(patrick.age)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=12,
            column=6,
        ),
        Result(
            type="error",
            message=(
                "Arguments missing for parameters "
                '"name", "age" (reportGeneralTypeIssues)'
            ),
            line=12,
            column=1,
        ),
        Result(
            type="information",
            message='Type of "patrick.name" is "str"',
            line=14,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "patrick.age" is "int"',
            line=15,
            column=13,
        ),
    ]

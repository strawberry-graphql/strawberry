from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]

CODE = """
import strawberry


@strawberry.interface
class Node:
    id: strawberry.ID

reveal_type(Node)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="information",
            message='Type of "Node" is "Type[Node]"',
            line=9,
            column=13,
        ),
    ]


CODE_2 = """
import strawberry


@strawberry.interface(name="nodeinterface")
class Node:
    id: strawberry.ID

reveal_type(Node)
"""


def test_pyright_calling():
    results = run_pyright(CODE_2)

    assert results == [
        Result(
            type="information",
            message='Type of "Node" is "Type[Node]"',
            line=9,
            column=13,
        ),
    ]

from .utils import Result, requires_pyright, run_pyright, skip_on_windows


pytestmark = [skip_on_windows, requires_pyright]


CODE = """
import strawberry


@strawberry.type(name="User")
class UserModel:
    name: str


@strawberry.input(name="User")
class UserInput:
    name: str


UserModel(name="Patrick")
UserModel(n="Patrick")

UserInput(name="Patrick")
UserInput(n="Patrick")
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=16,
            column=11,
        ),
        Result(
            type="error",
            message='Argument missing for parameter "name" (reportGeneralTypeIssues)',
            line=16,
            column=1,
        ),
        Result(
            type="error",
            message='No parameter named "n" (reportGeneralTypeIssues)',
            line=19,
            column=11,
        ),
        Result(
            type="error",
            message='Argument missing for parameter "name" (reportGeneralTypeIssues)',
            line=19,
            column=1,
        ),
    ]

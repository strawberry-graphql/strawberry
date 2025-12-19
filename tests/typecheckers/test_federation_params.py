from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]


CODE = """
import strawberry


@strawberry.federation.type(name="User")
class UserModel:
    name: str


UserModel(name="Patrick")
UserModel(n="Patrick")
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
            Result(type="error", message='No parameter named "n"', line=11, column=11),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Unexpected keyword argument "n" for "UserModel"',
                line=11,
                column=1,
            )
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="error",
                message="No argument provided for required parameter `name`",
                line=11,
                column=1,
            ),
            Result(
                type="error",
                message="Argument `n` does not match any known parameter",
                line=11,
                column=11,
            ),
        ]
    )

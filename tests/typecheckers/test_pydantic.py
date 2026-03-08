from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]

MYPY_PLUGINS = ["strawberry.ext.mypy_plugin", "pydantic.mypy"]

CODE = """
import pydantic
import strawberry

class UserModel(pydantic.BaseModel):
    age: int
    name: str

@strawberry.experimental.pydantic.type(model=UserModel)
class User:
    age: strawberry.auto
    name: strawberry.auto

user = User(age=1, name="abc")
reveal_type(user)
reveal_type(user.to_pydantic())
reveal_type(User.from_pydantic(UserModel(age=1, name="abc")))
"""


def test_pydantic_type():
    results = typecheck(CODE, mypy_plugins=MYPY_PLUGINS)

    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "mypy_test.User"',
                line=15,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "mypy_test.UserModel"',
                line=16,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "mypy_test.User"',
                line=17,
                column=13,
            ),
        ]
    )

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "user" is "StrawberryTypeFromPydantic[UserModel]"',
                line=15,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "user.to_pydantic()" is "UserModel"',
                line=16,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "User.from_pydantic(UserModel(age=1, name="abc"))" is "StrawberryTypeFromPydantic[UserModel]"',
                line=17,
                column=13,
            ),
        ]
    )

    # TY doesn't properly support this yet
    # assert results.ty == snapshot(...)  # noqa: ERA001

from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]

MYPY_PLUGINS = ["pydantic.mypy", "strawberry.ext.mypy_plugin"]

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


FIRST_CLASS_CODE = """
import pydantic
import strawberry

@strawberry.pydantic.type
class User(pydantic.BaseModel):
    age: int
    name: str

@strawberry.pydantic.input(name="CreateUserInput")
class CreateUserInput(pydantic.BaseModel):
    name: str

@strawberry.pydantic.interface
class Node(pydantic.BaseModel):
    id: str

user = User(age=1, name="abc")
reveal_type(user)
reveal_type(user.age)
reveal_type(CreateUserInput(name="abc"))
reveal_type(Node.model_validate({"id": "1"}))
"""


def test_first_class_pydantic_decorators_keep_the_model_type():
    results = typecheck(FIRST_CLASS_CODE, mypy_plugins=MYPY_PLUGINS)

    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "mypy_test.User"',
                line=19,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "int"',
                line=20,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "mypy_test.CreateUserInput"',
                line=21,
                column=13,
            ),
            Result(
                type="note",
                message='Revealed type is "mypy_test.Node"',
                line=22,
                column=13,
            ),
        ]
    )

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "user" is "User"',
                line=19,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "user.age" is "int"',
                line=20,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "CreateUserInput(name="abc")" is "CreateUserInput"',
                line=21,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "Node.model_validate({ "id": "1" })" is "Node"',
                line=22,
                column=13,
            ),
        ]
    )

    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `User`",
                line=19,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `int`",
                line=20,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `CreateUserInput`",
                line=21,
                column=13,
            ),
            Result(
                type="information",
                message="Revealed type: `Node`",
                line=22,
                column=13,
            ),
        ]
    )


RESOLVER_FIELD_CODE = """
import pydantic
import strawberry

@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def greeting(self, punctuation: str = "!") -> str:
        return self.name + punctuation

    @strawberry.pydantic.field(description="Shouted")
    async def shout(self) -> str:
        return self.name.upper()

user = User(name="Ada")
reveal_type(user.greeting)
reveal_type(user.greeting("?"))
reveal_type(user.shout)
"""


def test_resolver_fields_keep_the_method_type():
    results = typecheck(RESOLVER_FIELD_CODE, mypy_plugins=MYPY_PLUGINS)

    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "def (punctuation: str =) -> str"',
                line=18,
                column=13,
            ),
            Result(type="note", message='Revealed type is "str"', line=19, column=13),
            Result(
                type="note",
                message='Revealed type is "def () -> typing.Coroutine[Any, Any, str]"',
                line=20,
                column=13,
            ),
        ]
    )

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "user.greeting" is "(punctuation: str = "!") -> str"',
                line=18,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "user.greeting("?")" is "str"',
                line=19,
                column=13,
            ),
            Result(
                type="information",
                message='Type of "user.shout" is "() -> CoroutineType[Any, Any, str]"',
                line=20,
                column=13,
            ),
        ]
    )

    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message='Revealed type: `bound method User.greeting(punctuation: str = "!") -> str`',
                line=18,
                column=13,
            ),
            Result(
                type="information", message="Revealed type: `str`", line=19, column=13
            ),
            Result(
                type="information",
                message="Revealed type: `bound method User.shout() -> CoroutineType[Any, Any, str]`",
                line=20,
                column=13,
            ),
        ]
    )


UNKNOWN_ATTRIBUTE_CODE = """
import strawberry

strawberry.pydantic.type
strawberry.feild
"""


def test_lazy_pydantic_module_keeps_unknown_attributes_errors():
    results = typecheck(UNKNOWN_ATTRIBUTE_CODE, mypy_plugins=MYPY_PLUGINS)

    assert results.mypy == snapshot(
        [
            Result(
                type="error",
                message='Module has no attribute "feild"; maybe "field"?',
                line=5,
                column=1,
            )
        ]
    )
    assert results.pyright == snapshot(
        [
            Result(
                type="error", message='Type of "feild" is unknown', line=5, column=1
            ),
            Result(
                type="error",
                message='"feild" is not a known attribute of module "strawberry"',
                line=5,
                column=12,
            ),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="error",
                message="Module `strawberry` has no member `feild`",
                line=5,
                column=1,
            )
        ]
    )

from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


CODE = """
import strawberry

async def posts() -> strawberry.Streamable[str]:
    yield "🔥"


@strawberry.type
class User:
    name: str
    posts: strawberry.Streamable[str] = strawberry.field(resolver=posts)

patrick = User(name="Patrick")

reveal_type(patrick.name)
reveal_type(patrick.posts)
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="information",
            message='Type of "patrick.name" is "str"',
            line=15,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "patrick.posts" is "AsyncGenerator[str, None]"',
            line=16,
            column=13,
        ),
    ]

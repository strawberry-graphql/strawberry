from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]

CODE_ROUTER_WITH_CONTEXT = """
import strawberry

from strawberry.fastapi import GraphQLRouter, BaseContext


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


class Context(BaseContext):
    pass


def get_context() -> Context:
    return Context()


router = GraphQLRouter(
    strawberry.Schema(
        query=Query,
    ),
    context_getter=get_context,
)

reveal_type(router)
"""


def test_router_with_context():
    results = typecheck(CODE_ROUTER_WITH_CONTEXT)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "router" is "GraphQLRouter[Context, None]"',
                line=29,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "strawberry.fastapi.router.GraphQLRouter[mypy_test.Context, None]"',
                line=29,
                column=13,
            ),
        ]
    )


CODE_ROUTER_WITH_ASYNC_CONTEXT = """
import strawberry

from strawberry.fastapi import GraphQLRouter, BaseContext


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


class Context(BaseContext):
    pass


async def get_context() -> Context:
    return Context()


router = GraphQLRouter[Context](
    strawberry.Schema(
        query=Query,
    ),
    context_getter=get_context,
)

reveal_type(router)
"""


def test_router_with_async_context():
    results = typecheck(CODE_ROUTER_WITH_ASYNC_CONTEXT)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "router" is "GraphQLRouter[Context, None]"',
                line=29,
                column=13,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(
                type="note",
                message='Revealed type is "strawberry.fastapi.router.GraphQLRouter[mypy_test.Context, None]"',
                line=29,
                column=13,
            ),
        ]
    )

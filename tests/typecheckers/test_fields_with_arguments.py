from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, skip_on_windows
from .utils.typecheck import typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy]


CODE = """
import strawberry


@strawberry.type
class Query:
    @strawberry.field(description="Get the last user")
    def last_user_v2(self) -> str:
        return "Hello"

@strawberry.federation.type
class FederatedQuery:
    @strawberry.federation.field(description="Get the last user")
    def last_user_v2(self) -> str:
        return "Hello"
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot([])
    assert results.mypy == snapshot([])

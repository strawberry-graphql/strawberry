from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]

CODE = """
from typing_extensions import TypeAlias
import strawberry

StrSubscriptionResult: TypeAlias = strawberry.subscription_result(str)  # type: ignore

reveal_type(StrSubscriptionResult)

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def time(self) -> StrSubscriptionResult:
        ...
"""


def test_pyright():
    results = run_pyright(CODE)

    assert results == [
        Result(
            type="information",
            message='Type of "StrSubscriptionResult" is "Unknown"',
            line=7,
            column=13,
        ),
        Result(
            type="error",
            message="Declared return type is unknown (reportUnknownVariableType)",
            line=12,
            column=29,
        ),
    ]

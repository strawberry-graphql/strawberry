from .utils import requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]

CODE_ASYNCGENERATOR = """
import typing

import strawberry

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def time(self) -> typing.AsyncGenerator[str, None]:
        ...
"""

CODE = """
import strawberry

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def time(self) -> strawberry.SubscriptionResult[str]:
        ...
"""


def test_pyright():
    results_asyncgenerator = run_pyright(CODE_ASYNCGENERATOR)
    results_subscriptionresult = run_pyright(CODE)

    assert results_asyncgenerator == results_subscriptionresult
    assert len(results_subscriptionresult) == 0

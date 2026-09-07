import asyncio
from collections.abc import Iterator

import pytest


@pytest.fixture
def benchmark_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Exclude loop creation and shutdown from steady-state measurements."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()

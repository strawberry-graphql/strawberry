import pytest_asyncio

from tests.aiohttp.app import create_app


@pytest_asyncio.fixture
async def aiohttp_app_client(event_loop, aiohttp_client):
    app = create_app(graphiql=True)
    event_loop.set_debug(True)
    return await aiohttp_client(app)

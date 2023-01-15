import pytest

from strawberry.channels.handlers.ws_handler import GraphQLWSConsumer
from strawberry.channels.testing import GqlWsCommunicator

from .schema import schema

application = GraphQLWSConsumer.as_asgi(schema=schema, keep_alive_interval=50)


@pytest.fixture
async def communicator():
    com = GqlWsCommunicator(application=application, path="/graphql")
    await com.gql_init()
    return com


async def test_subscribe(communicator):

    async for res in communicator.subscribe(
        query='subscription { echo(message: "Hi") }'
    ):
        assert res.data == {"echo": "Hi"}

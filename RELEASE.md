Release type: patch

Add `GqlWsCommunicator` for testing websockets on channels.
i.e:

```python
import pytest
from strawberry.channels.testing import GqlWsCommunicator
from myapp.asgi import application


@pytest.fixture
async def gql_communicator():
    async with GqlWsCommunicator(application=application, path="/graphql") as client:
        yield client


async def test_subscribe_echo(gql_communicator):
    async for res in gql_communicator.subscribe(
        query='subscription { echo(message: "Hi") }'
    ):
        assert res.data == {"echo": "Hi"}
```

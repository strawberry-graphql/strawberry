from .clients.base import HttpClient

# TODO: do multipart subscriptions work on both GET and POST?


async def test_graphql_query(http_client: HttpClient):
    response = await http_client.post(
        url="/graphql",
        json={
            "query": 'subscription { echo(message: "Hello world", delay: 0.2) }',
        },
        headers={
            # TODO: this header might just be for django
            "CONTENT_TYPE": "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json",
        },
    )

    data = [d async for d in response.streaming_json()]

    assert data == [{'data': {'echo': 'Hello world'}}]

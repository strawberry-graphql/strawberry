import json

import pytest
from channels.testing import HttpCommunicator

import strawberry
from strawberry.channels import GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer
from strawberry.schema.config import StrawberryConfig
from tests.views.schema import Query


@pytest.mark.parametrize(
    "consumer_class", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer]
)
@pytest.mark.parametrize("return_bytes", [False, True], ids=["str", "bytes"])
@pytest.mark.parametrize("batch", [False, True], ids=["single", "batch"])
@pytest.mark.parametrize("with_error", [False, True], ids=["success", "error"])
async def test_encode_json_override(consumer_class, return_bytes, batch, with_error):
    encoded_inputs = []
    encoded_outputs = []

    class CustomConsumer(consumer_class):
        def encode_json(self, data: object) -> str | bytes:
            encoded_inputs.append(data)
            # Distinct formatting and non-ASCII text expose bypasses or re-encoding.
            content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            result = content.encode() if return_bytes else content
            encoded_outputs.append(result)
            return result

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(batching_config={"max_operations": 10}),
    )
    query = '{ teapot setHeader(name: "Strawberry") }'
    if with_error:
        query = "{ missingField }"
    operation = {"query": query}
    body = [operation, operation] if batch else operation
    communicator = HttpCommunicator(
        CustomConsumer.as_asgi(schema=schema),
        "POST",
        "/graphql",
        body=json.dumps(body).encode(),
        headers=[(b"content-type", b"application/json")],
    )

    response = await communicator.get_response()

    assert len(encoded_inputs) == 1
    assert len(encoded_outputs) == 1
    output = encoded_outputs[0]
    assert response["body"] == (output if return_bytes else output.encode())
    if return_bytes:
        assert response["body"] is output
    assert response["status"] == (200 if with_error else 418)
    headers = dict(response["headers"])
    assert headers[b"Content-Type"] == b"application/json"
    if not with_error:
        assert headers[b"X-Name"] == b"Strawberry"
    data = json.loads(response["body"])
    assert data == encoded_inputs[0]
    results = data if batch else [data]
    assert len(results) == (2 if batch else 1)
    for result in results:
        if with_error:
            assert result["data"] is None
            assert "missingField" in result["errors"][0]["message"]
        else:
            assert result == {"data": {"teapot": "🫖", "setHeader": "Strawberry"}}

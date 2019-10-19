import base64

import pytest

import strawberry
from strawberry.graphql import execute


Base64Encoded = strawberry.scalar(bytes, serialize=base64.b64encode)


@pytest.mark.asyncio
async def test_custom_scalar_serialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def custom_scalar_field(self, info) -> Base64Encoded:
            return Base64Encoded(b"decoded value")

    schema = strawberry.Schema(Query)

    result = await execute(schema, "{ customScalarField }")

    assert not result.errors
    assert base64.b64decode(result.data["customScalarField"]) == b"decoded value"

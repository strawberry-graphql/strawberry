import base64
from typing import NewType

import pytest

import strawberry
from strawberry.graphql import execute


Base64Encoded = strawberry.scalar(
    NewType("Base64Encoded", bytes),
    serialize=base64.b64encode,
    parse_value=base64.b64decode,
)


@strawberry.scalar(serialize=lambda x: 42, parse_value=lambda x: Always42())
class Always42:
    pass


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


@pytest.mark.asyncio
async def test_custom_scalar_deserialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def decode_base64(self, info, encoded: Base64Encoded) -> str:
            return bytes(encoded).decode("ascii")

    schema = strawberry.Schema(Query)

    encoded = base64.b64encode(b"decoded").decode("ascii")
    result = await execute(schema, f'{{ decodeBase64(encoded: "{encoded}") }}')

    assert not result.errors
    assert result.data["decodeBase64"] == "decoded"


@pytest.mark.asyncio
async def test_custom_scalar_decorated_class():
    @strawberry.type
    class Query:
        @strawberry.field
        def answer(self, info) -> Always42:
            return Always42()

    schema = strawberry.Schema(Query)

    result = await execute(schema, "{ answer }")

    assert not result.errors
    assert result.data["answer"] == 42

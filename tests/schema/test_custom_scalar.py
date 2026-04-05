import base64
from typing import NewType

import strawberry
from strawberry.schema.config import StrawberryConfig

# Define the types
Base64Encoded = NewType("Base64Encoded", bytes)


class Always42:
    pass


MyStr = NewType("MyStr", str)


def test_custom_scalar_serialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def custom_scalar_field(self) -> Base64Encoded:
            return Base64Encoded(b"decoded value")

    schema = strawberry.Schema(
        Query,
        config=StrawberryConfig(
            scalar_map={
                Base64Encoded: strawberry.scalar(
                    name="Base64Encoded",
                    serialize=base64.b64encode,
                    parse_value=base64.b64decode,
                )
            }
        ),
    )

    result = schema.execute_sync("{ customScalarField }")

    assert not result.errors
    assert base64.b64decode(result.data["customScalarField"]) == b"decoded value"


def test_custom_scalar_deserialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def decode_base64(self, encoded: Base64Encoded) -> str:
            return bytes(encoded).decode("ascii")

    schema = strawberry.Schema(
        Query,
        config=StrawberryConfig(
            scalar_map={
                Base64Encoded: strawberry.scalar(
                    name="Base64Encoded",
                    serialize=base64.b64encode,
                    parse_value=base64.b64decode,
                )
            }
        ),
    )

    encoded = Base64Encoded(base64.b64encode(b"decoded"))
    query = """query decode($encoded: Base64Encoded!) {
        decodeBase64(encoded: $encoded)
    }"""
    result = schema.execute_sync(query, variable_values={"encoded": encoded})

    assert not result.errors
    assert result.data["decodeBase64"] == "decoded"


def test_custom_scalar_decorated_class():
    @strawberry.type
    class Query:
        @strawberry.field
        def answer(self) -> Always42:
            return Always42()

    schema = strawberry.Schema(
        Query,
        config=StrawberryConfig(
            scalar_map={
                Always42: strawberry.scalar(
                    name="Always42",
                    serialize=lambda x: 42,
                    parse_value=lambda x: Always42(),
                )
            }
        ),
    )

    result = schema.execute_sync("{ answer }")

    assert not result.errors
    assert result.data["answer"] == 42


def test_custom_scalar_default_serialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def my_str(self, arg: MyStr) -> MyStr:
            return MyStr(str(arg) + "Suffix")

    schema = strawberry.Schema(
        Query,
        config=StrawberryConfig(
            scalar_map={
                MyStr: strawberry.scalar(
                    name="MyStr",
                )
            }
        ),
    )

    result = schema.execute_sync('{ myStr(arg: "value") }')

    assert not result.errors
    assert result.data["myStr"] == "valueSuffix"

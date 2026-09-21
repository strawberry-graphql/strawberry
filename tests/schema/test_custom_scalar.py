import base64
from typing import NewType

import strawberry
from strawberry.exceptions import StrawberryInputCoercionError
from strawberry.schema.config import StrawberryConfig

Base64Encoded = strawberry.scalar(
    NewType("Base64Encoded", bytes),
    serialize=base64.b64encode,
    parse_value=base64.b64decode,
)


@strawberry.scalar(serialize=lambda x: 42, parse_value=lambda x: Always42())
class Always42:
    pass


MyStr = strawberry.scalar(NewType("MyStr", str))


def test_custom_scalar_serialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def custom_scalar_field(self) -> Base64Encoded:
            return Base64Encoded(b"decoded value")

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ customScalarField }")

    assert not result.errors
    assert base64.b64decode(result.data["customScalarField"]) == b"decoded value"


def test_custom_scalar_deserialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def decode_base64(self, encoded: Base64Encoded) -> str:
            return bytes(encoded).decode("ascii")

    schema = strawberry.Schema(Query)

    encoded = Base64Encoded(base64.b64encode(b"decoded"))
    query = """query decode($encoded: Base64Encoded!) {
        decodeBase64(encoded: $encoded)
    }"""
    result = schema.execute_sync(query, variable_values={"encoded": encoded})

    assert not result.errors
    assert result.data["decodeBase64"] == "decoded"


def test_custom_scalar_input_errors_can_be_classified():
    CustomValue = NewType("CustomValue", str)

    def parse_value(value: object) -> CustomValue:
        raise StrawberryInputCoercionError(f"Invalid value: {value}")

    @strawberry.type
    class Query:
        @strawberry.field
        def parse(self, value: CustomValue) -> bool:  # pragma: no cover
            return True

    schema = strawberry.Schema(
        Query,
        config=StrawberryConfig(
            scalar_map={
                CustomValue: strawberry.scalar(
                    name="CustomValue",
                    serialize=str,
                    parse_value=parse_value,
                )
            }
        ),
    )

    literal_result = schema.execute_sync('{ parse(value: "invalid") }')
    variable_result = schema.execute_sync(
        "query($value: CustomValue!) { parse(value: $value) }",
        variable_values={"value": "invalid"},
    )

    assert literal_result.errors
    assert isinstance(literal_result.errors[0], StrawberryInputCoercionError)
    assert variable_result.errors
    assert isinstance(
        variable_result.errors[0].original_error, StrawberryInputCoercionError
    )


def test_custom_scalar_decorated_class():
    @strawberry.type
    class Query:
        @strawberry.field
        def answer(self) -> Always42:
            return Always42()

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ answer }")

    assert not result.errors
    assert result.data["answer"] == 42


def test_custom_scalar_default_serialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def my_str(self, arg: MyStr) -> MyStr:
            return MyStr(str(arg) + "Suffix")

    schema = strawberry.Schema(Query)

    result = schema.execute_sync('{ myStr(arg: "value") }')

    assert not result.errors
    assert result.data["myStr"] == "valueSuffix"

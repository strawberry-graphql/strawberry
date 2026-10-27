import base64
from datetime import UTC, datetime, timedelta
from typing import Annotated, Generic, NewType, TypeVar

import pytest

import strawberry
import strawberry.federation
from strawberry.exceptions import (
    ScalarAlreadyRegisteredError,
    StrawberryInputCoercionError,
)
from strawberry.schema.config import StrawberryConfig

# Define the types
Base64Encoded = NewType("Base64Encoded", bytes)


class Always42:
    pass


MyStr = NewType("MyStr", str)

_EpochDateTime = NewType("_EpochDateTime", datetime)
EpochDateTime = Annotated[
    _EpochDateTime,
    strawberry.scalar(
        name="EpochDateTime",
        description="Seconds since the Unix epoch",
        specified_by_url="https://example.com/epoch",
        serialize=lambda value: int(value.timestamp()),
        parse_value=lambda value: datetime.fromtimestamp(value, UTC),
    ),
]


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


@pytest.mark.parametrize("federation", [False, True])
@pytest.mark.parametrize("variables", [False, True])
async def test_annotated_scalar_inputs_and_outputs(federation, variables):
    @strawberry.input
    class Input:
        values: list[list[EpochDateTime | None]]
        maybe: strawberry.Maybe[EpochDateTime]
        default: EpochDateTime = datetime(1970, 1, 1, tzinfo=UTC)

    @strawberry.type
    class Query:
        @strawberry.field
        async def echo(
            self,
            input: Input,
            value: Annotated[EpochDateTime, strawberry.argument(name="at")],
        ) -> list[EpochDateTime | None]:
            assert value == datetime(1970, 1, 1, 0, 2, 3, tzinfo=UTC)
            assert input.values == [[None, value]]
            assert input.maybe == strawberry.Some(value)
            assert input.default == datetime(1970, 1, 1, tzinfo=UTC)
            return [None, value + timedelta(seconds=60)]

    schema_class = strawberry.federation.Schema if federation else strawberry.Schema
    schema = schema_class(Query)
    if variables:
        result = await schema.execute(
            "query($input: Input!, $at: EpochDateTime!) { echo(input: $input, at: $at) }",
            variable_values={
                "input": {"values": [[None, 123]], "maybe": 123},
                "at": 123,
            },
        )
    else:
        result = await schema.execute(
            "{ echo(input: {values: [[null, 123]], maybe: 123}, at: 123) }"
        )

    assert result.errors is None
    assert result.data == {"echo": [None, 183]}
    definition = schema._schema.get_type("EpochDateTime")
    assert definition.description == "Seconds since the Unix epoch"
    assert definition.specified_by_url == "https://example.com/epoch"
    assert "default: EpochDateTime! = 0" in str(schema)


@pytest.mark.parametrize("key", [EpochDateTime, _EpochDateTime])
@pytest.mark.parametrize("legacy_overrides", [False, True])
def test_annotated_scalar_schema_overrides(key, legacy_overrides):
    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: EpochDateTime) -> EpochDateTime:
            assert value == 21
            return value + 1

    definition = strawberry.scalar(
        name="EpochDateTime",
        serialize=lambda value: value * 3,
        parse_value=lambda value: value + 1,
    )
    config = StrawberryConfig(scalar_map={key: definition})
    kwargs = {}
    if legacy_overrides:
        # scalar_overrides retains precedence over config.scalar_map.
        config.scalar_map = {key: strawberry.scalar(name="Wrong")}
        kwargs["scalar_overrides"] = {key: definition}
    schema = strawberry.Schema(Query, config=config, **kwargs)
    result = schema.execute_sync("{ echo(value: 20) }")
    assert result.errors is None
    assert result.data == {"echo": 66}


def test_annotated_scalar_does_not_replace_builtin():
    LocalTimestamp = Annotated[
        datetime,
        strawberry.scalar(name="LocalTimestamp", serialize=lambda value: 17),
    ]

    @strawberry.type
    class Query:
        local: LocalTimestamp
        normal: datetime
        nullable: Annotated[datetime | None, strawberry.scalar(name="Nullable")]

    schema = strawberry.Schema(Query)
    result = schema.execute_sync(
        "{ local normal nullable }",
        root_value=Query(
            local=datetime(2020, 1, 2),
            normal=datetime(2020, 1, 2),
            nullable=None,
        ),
    )
    assert result.errors is None
    assert result.data == {
        "local": 17,
        "normal": "2020-01-02T00:00:00",
        "nullable": None,
    }
    assert "nullable: Nullable\n" in str(schema)

    override_schema = strawberry.Schema(
        Query,
        config=StrawberryConfig(
            scalar_map={
                datetime: strawberry.scalar(name="DateTime", serialize=lambda value: 99)
            }
        ),
    )
    result = override_schema.execute_sync(
        "{ local normal nullable }",
        root_value=Query(
            local=datetime(2020, 1, 2), normal=datetime(2020, 1, 2), nullable=None
        ),
    )
    assert result.errors is None
    assert result.data == {"local": 99, "normal": 99, "nullable": None}


def test_annotated_scalars_reject_conflicting_names():
    First = Annotated[str, strawberry.scalar(name="Duplicate", serialize=str)]
    Second = Annotated[int, strawberry.scalar(name="Duplicate", serialize=int)]

    @strawberry.type
    class Query:
        first: First
        second: Second

    with pytest.raises(
        ScalarAlreadyRegisteredError,
        match="Scalar `Duplicate` has already been registered",
    ):
        strawberry.Schema(Query)


def test_annotated_scalar_in_generic_type():
    T = TypeVar("T")

    @strawberry.type
    class Container(Generic[T]):
        value: T

    @strawberry.type
    class Query:
        container: Container[EpochDateTime]

    schema = strawberry.Schema(Query)
    result = schema.execute_sync(
        "{ container { value } }",
        root_value=Query(
            container=Container(value=datetime(1970, 1, 1, 0, 2, 3, tzinfo=UTC))
        ),
    )
    assert result.errors is None
    assert result.data == {"container": {"value": 123}}
    assert "type EpochDateTimeContainer" in str(schema)

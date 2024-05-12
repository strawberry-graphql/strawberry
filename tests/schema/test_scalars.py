import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from textwrap import dedent
from typing import Optional
from uuid import UUID

import pytest

import strawberry
from strawberry import scalar
from strawberry.exceptions import ScalarAlreadyRegisteredError
from strawberry.scalars import JSON, Base16, Base32, Base64
from strawberry.schema.types.base_scalars import Date


def test_void_function():
    NoneType = type(None)

    @strawberry.type
    class Query:
        @strawberry.field
        def void_ret(self) -> None:
            return

        @strawberry.field
        def void_ret_crash(self) -> NoneType:
            return 1

        @strawberry.field
        def void_arg(self, x: None) -> None:
            return

    schema = strawberry.Schema(query=Query)

    assert (
        str(schema)
        == dedent(
            '''
      type Query {
        voidRet: Void
        voidRetCrash: Void
        voidArg(x: Void): Void
      }

      """Represents NULL values"""
      scalar Void
    '''
        ).strip()
    )

    result = schema.execute_sync("query { voidRet }")
    assert not result.errors
    assert result.data == {
        "voidRet": None,
    }

    result = schema.execute_sync("query { voidArg (x: null) }")
    assert not result.errors
    assert result.data == {
        "voidArg": None,
    }

    result = schema.execute_sync("query { voidArg (x: 1) }")
    assert result.errors

    result = schema.execute_sync("query { voidRetCrash }")
    assert result.errors


def test_uuid_field_string_value():
    @strawberry.type
    class Query:
        unique_id: UUID

    schema = strawberry.Schema(query=Query)

    assert (
        str(schema)
        == dedent(
            """
      type Query {
        uniqueId: UUID!
      }

      scalar UUID
    """
        ).strip()
    )

    result = schema.execute_sync(
        "query { uniqueId }",
        root_value=Query(
            unique_id="e350746c-33b6-4469-86b0-5f16e1e12232",
        ),
    )
    assert not result.errors
    assert result.data == {
        "uniqueId": "e350746c-33b6-4469-86b0-5f16e1e12232",
    }


def test_uuid_field_uuid_value():
    @strawberry.type
    class Query:
        unique_id: UUID

    schema = strawberry.Schema(query=Query)

    assert (
        str(schema)
        == dedent(
            """
      type Query {
        uniqueId: UUID!
      }

      scalar UUID
    """
        ).strip()
    )

    result = schema.execute_sync(
        "query { uniqueId }",
        root_value=Query(
            unique_id=UUID("e350746c-33b6-4469-86b0-5f16e1e12232"),
        ),
    )
    assert not result.errors
    assert result.data == {
        "uniqueId": "e350746c-33b6-4469-86b0-5f16e1e12232",
    }


def test_uuid_input():
    @strawberry.type
    class Query:
        ok: bool

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def uuid_input(self, input_id: UUID) -> str:
            assert isinstance(input_id, UUID)
            return str(input_id)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            uuidInput(inputId: "e350746c-33b6-4469-86b0-5f16e1e12232")
        }
    """
    )

    assert not result.errors
    assert result.data == {
        "uuidInput": "e350746c-33b6-4469-86b0-5f16e1e12232",
    }


def test_json():
    @strawberry.type
    class Query:
        @strawberry.field
        def echo_json(data: JSON) -> JSON:
            return data

        @strawberry.field
        def echo_json_nullable(data: Optional[JSON]) -> Optional[JSON]:
            return data

    schema = strawberry.Schema(query=Query)

    expected_schema = dedent(
        '''
        """
        The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
        """
        scalar JSON @specifiedBy(url: "https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf")

        type Query {
          echoJson(data: JSON!): JSON!
          echoJsonNullable(data: JSON): JSON
        }
        '''
    ).strip()

    assert str(schema) == expected_schema

    result = schema.execute_sync(
        """
        query {
            echoJson(data: {hello: {a: 1}, someNumbers: [1, 2, 3], null: null})
            echoJsonNullable(data: {hello: {a: 1}, someNumbers: [1, 2, 3], null: null})
        }
    """
    )

    assert not result.errors
    assert result.data == {
        "echoJson": {"hello": {"a": 1}, "someNumbers": [1, 2, 3], "null": None},
        "echoJsonNullable": {"hello": {"a": 1}, "someNumbers": [1, 2, 3], "null": None},
    }

    result = schema.execute_sync(
        """
        query {
            echoJson(data: null)
        }
    """
    )
    assert result.errors  # echoJson is not-null null

    result = schema.execute_sync(
        """
        query {
            echoJsonNullable(data: null)
        }
    """
    )
    assert not result.errors
    assert result.data == {
        "echoJsonNullable": None,
    }


def test_base16():
    @strawberry.type
    class Query:
        @strawberry.field
        def base16_encode(data: str) -> Base16:
            return bytes(data, "utf-8")

        @strawberry.field
        def base16_decode(data: Base16) -> str:
            return data.decode("utf-8")

        @strawberry.field
        def base32_encode(data: str) -> Base32:
            return bytes(data, "utf-8")

        @strawberry.field
        def base32_decode(data: Base32) -> str:
            return data.decode("utf-8")

        @strawberry.field
        def base64_encode(data: str) -> Base64:
            return bytes(data, "utf-8")

        @strawberry.field
        def base64_decode(data: Base64) -> str:
            return data.decode("utf-8")

    schema = strawberry.Schema(query=Query)

    assert (
        str(schema)
        == dedent(
            '''
        """Represents binary data as Base16-encoded (hexadecimal) strings."""
        scalar Base16 @specifiedBy(url: "https://datatracker.ietf.org/doc/html/rfc4648.html#section-8")

        """
        Represents binary data as Base32-encoded strings, using the standard alphabet.
        """
        scalar Base32 @specifiedBy(url: "https://datatracker.ietf.org/doc/html/rfc4648.html#section-6")

        """
        Represents binary data as Base64-encoded strings, using the standard alphabet.
        """
        scalar Base64 @specifiedBy(url: "https://datatracker.ietf.org/doc/html/rfc4648.html#section-4")

        type Query {
          base16Encode(data: String!): Base16!
          base16Decode(data: Base16!): String!
          base32Encode(data: String!): Base32!
          base32Decode(data: Base32!): String!
          base64Encode(data: String!): Base64!
          base64Decode(data: Base64!): String!
        }
    '''
        ).strip()
    )

    result = schema.execute_sync(
        """
        query {
            base16Encode(data: "Hello")
            base16Decode(data: "48656c6C6f")  # < Mix lowercase and uppercase
            base32Encode(data: "Hello")
            base32Decode(data: "JBSWY3dp")  # < Mix lowercase and uppercase
            base64Encode(data: "Hello")
            base64Decode(data: "SGVsbG8=")
        }
    """
    )

    assert not result.errors
    assert result.data == {
        "base16Encode": "48656C6C6F",
        "base16Decode": "Hello",
        "base32Encode": "JBSWY3DP",
        "base32Decode": "Hello",
        "base64Encode": "SGVsbG8=",
        "base64Decode": "Hello",
    }


def test_override_built_in_scalars():
    EpochDateTime = strawberry.scalar(
        datetime,
        serialize=lambda value: int(value.timestamp()),
        parse_value=lambda value: datetime.fromtimestamp(int(value), timezone.utc),
    )

    @strawberry.type
    class Query:
        @strawberry.field
        def current_time(self) -> datetime:
            return datetime(2021, 8, 11, 12, 0, tzinfo=timezone.utc)

        @strawberry.field
        def isoformat(self, input_datetime: datetime) -> str:
            return input_datetime.isoformat()

    schema = strawberry.Schema(
        Query,
        scalar_overrides={
            datetime: EpochDateTime,
        },
    )

    result = schema.execute_sync(
        """
        {
            currentTime
            isoformat(inputDatetime: 1628683200)
        }
        """
    )

    assert not result.errors
    assert result.data["currentTime"] == 1628683200
    assert result.data["isoformat"] == "2021-08-11T12:00:00+00:00"


def test_override_unknown_scalars():
    Duration = strawberry.scalar(
        timedelta,
        name="Duration",
        serialize=timedelta.total_seconds,
        parse_value=lambda s: timedelta(seconds=s),
    )

    @strawberry.type
    class Query:
        @strawberry.field
        def duration(self, value: timedelta) -> timedelta:
            return value

    schema = strawberry.Schema(Query, scalar_overrides={timedelta: Duration})

    result = schema.execute_sync("{ duration(value: 10) }")

    assert not result.errors
    assert result.data == {"duration": 10}


def test_decimal():
    @strawberry.type
    class Query:
        @strawberry.field
        def decimal(value: Decimal) -> Decimal:
            return value

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            floatDecimal: decimal(value: 3.14)
            floatDecimal2: decimal(value: 3.14509999)
            floatDecimal3: decimal(value: 0.000001)
            stringDecimal: decimal(value: "3.14")
            stringDecimal2: decimal(value: "3.1499999991")
        }
    """
    )

    assert not result.errors
    assert result.data == {
        "floatDecimal": "3.14",
        "floatDecimal2": "3.14509999",
        "floatDecimal3": "0.000001",
        "stringDecimal": "3.14",
        "stringDecimal2": "3.1499999991",
    }


@pytest.mark.raises_strawberry_exception(
    ScalarAlreadyRegisteredError,
    match="Scalar `MyCustomScalar` has already been registered",
)
def test_duplicate_scalars_raises_exception():
    MyCustomScalar = strawberry.scalar(
        str,
        name="MyCustomScalar",
    )

    MyCustomScalar2 = strawberry.scalar(
        int,
        name="MyCustomScalar",
    )

    @strawberry.type
    class Query:
        scalar_1: MyCustomScalar
        scalar_2: MyCustomScalar2

    strawberry.Schema(Query)


@pytest.mark.raises_strawberry_exception(
    ScalarAlreadyRegisteredError,
    match="Scalar `MyCustomScalar` has already been registered",
)
def test_duplicate_scalars_raises_exception_using_alias():
    MyCustomScalar = scalar(
        str,
        name="MyCustomScalar",
    )

    MyCustomScalar2 = scalar(
        int,
        name="MyCustomScalar",
    )

    @strawberry.type
    class Query:
        scalar_1: MyCustomScalar
        scalar_2: MyCustomScalar2

    strawberry.Schema(Query)


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="pipe syntax for union is only available on python 3.10+",
)
def test_optional_scalar_with_or_operator():
    """Check `|` operator support with an optional scalar."""

    @strawberry.type
    class Query:
        date: Date | None

    schema = strawberry.Schema(query=Query)

    query = "{ date }"

    result = schema.execute_sync(query, root_value=Query(date=None))
    assert not result.errors
    assert result.data["date"] is None

    result = schema.execute_sync(query, root_value=Query(date=date(2020, 1, 1)))
    assert not result.errors
    assert result.data["date"] == "2020-01-01"

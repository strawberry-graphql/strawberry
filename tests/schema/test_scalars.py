from datetime import datetime, timezone
from textwrap import dedent
from uuid import UUID

import strawberry


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


def test_override_built_in_scalars():
    EpocDateTime = strawberry.scalar(
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

    class CustomSchema(strawberry.Schema):
        def get_scalar(self, scalar):
            if scalar == datetime:
                return EpocDateTime
            return super().get_scalar(scalar)

    schema = CustomSchema(Query)

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

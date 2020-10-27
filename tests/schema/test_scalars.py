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

from dataclasses import dataclass

from strawberry import Schema, field
from strawberry import type as graphql_type
from strawberry.field import SupportedSchema
from strawberry.identifier import SchemaIdentifier, default_version_comparator


@graphql_type
class Query:
    @field(name="name")
    def get_name(self) -> str:
        return "Jane Doe"

    @field(name="debugMessage", supported_schemas=[SupportedSchema(name="internal")])
    def get_debug_message(self) -> str:
        return "Something to help debug."

    @field(
        name="riskScore",
        supported_schemas=[SupportedSchema(name="internal", until_version="2")],
    )
    def get_risk_score_old(self) -> float:
        return 4.2

    @field(
        name="riskScore",
        supported_schemas=[SupportedSchema(name="internal", from_version="3")],
    )
    def get_risk_score_new(self) -> float:
        return 42


def test_version_comparison():
    assert default_version_comparator("1", "2") == -1
    assert default_version_comparator("1", "1") == 0
    assert default_version_comparator("2", "1") == 1
    assert default_version_comparator("2023-01-01", "2024-01-01") == -1
    assert default_version_comparator("2023-01-01", "2023-01-01") == 0
    assert default_version_comparator("2023-01-01", "2022-01-01") == 1
    assert default_version_comparator("1.2.3", "1.2.4") == -1
    assert default_version_comparator("1.2.3", "1.2.3") == 0
    assert default_version_comparator("1.2.3", "1.2.2") == 1
    assert default_version_comparator("1.2.3", "1") == 1
    assert default_version_comparator("1.2.3", "1.3") == -1


internal_schema_v1 = Schema(
    schema_identifier=SchemaIdentifier(name="internal", version="1"), query=Query
)
internal_schema_v3 = Schema(
    schema_identifier=SchemaIdentifier(name="internal", version="3"), query=Query
)
external_schema = Schema(
    schema_identifier=SchemaIdentifier(name="external", version=""), query=Query
)
plain_schema = Schema(query=Query)

internal_query = "{ name, debugMessage, riskScore }"


def test_base_fields():
    # Every schema can select the `name` field
    result = internal_schema_v1.execute_sync("{ name }", root_value=Query())
    assert not result.errors
    assert result.data["name"] == "Jane Doe"

    result = internal_schema_v3.execute_sync("{ name }", root_value=Query())
    assert not result.errors
    assert result.data["name"] == "Jane Doe"

    result = external_schema.execute_sync("{ name }", root_value=Query())
    assert not result.errors
    assert result.data["name"] == "Jane Doe"

    result = plain_schema.execute_sync("{ name }", root_value=Query())
    assert not result.errors
    assert result.data["name"] == "Jane Doe"


def test_supported_fields_by_schema_name():
    # Internal schemas can select the `debugMessage` but not the external schema
    result = internal_schema_v1.execute_sync("{ debugMessage }", root_value=Query())
    assert not result.errors
    assert result.data["debugMessage"] == "Something to help debug."

    result = internal_schema_v3.execute_sync("{ debugMessage }", root_value=Query())
    assert not result.errors
    assert result.data["debugMessage"] == "Something to help debug."

    result = external_schema.execute_sync("{ debugMessage }", root_value=Query())
    assert result.errors

    result = plain_schema.execute_sync("{ debugMessage }", root_value=Query())
    assert result.errors


def test_supported_fields_by_version():
    # Version 1 of internal schema selects the old riskScore
    result = internal_schema_v1.execute_sync("{ riskScore }", root_value=Query())
    assert not result.errors
    assert result.data["riskScore"] == 4.2

    # Version 3 of internal schema selects the new riskScore
    result = internal_schema_v3.execute_sync("{ riskScore }", root_value=Query())
    assert not result.errors
    assert result.data["riskScore"] == 42

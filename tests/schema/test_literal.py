from enum import Enum
from textwrap import dedent
from typing import Literal

import pytest

import strawberry
from strawberry.types.literal import is_valid_literal_value


def test_literal_fields_use_the_underlying_scalar_type() -> None:
    @strawberry.type
    class Query:
        status: Literal["ready"]
        priority: Literal[1, 2]
        enabled: Literal[True]

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          status: String!
          priority: Int!
          enabled: Boolean!
        }"""
    )

    result = schema.execute_sync(
        "{ status priority enabled }",
        root_value=Query(status="ready", priority=2, enabled=True),
    )

    assert not result.errors
    assert result.data == {"status": "ready", "priority": 2, "enabled": True}


def test_literal_string_annotation_is_resolved() -> None:
    @strawberry.type
    class Query:
        status: 'Literal["ready"]'

    schema = strawberry.Schema(query=Query)

    assert "status: String!" in str(schema)


def test_literal_argument_accepts_an_allowed_value() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: Literal["one", "two"]) -> str:
            return value

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync('{ echo(value: "two") }')

    assert not result.errors
    assert result.data == {"echo": "two"}


def test_literal_argument_rejects_a_disallowed_value() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: Literal["one", "two"]) -> str:
            return value

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync('{ echo(value: "three") }')

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == (
        "Expected value to be one of ('one', 'two'); received 'three'"
    )


def test_literals_work_in_nested_optional_and_list_inputs() -> None:
    @strawberry.input
    class Settings:
        mode: Literal["fast", "safe"]
        retries: Literal[1, 2, 3] | None
        flags: list[Literal[True, False]]

    @strawberry.type
    class Query:
        @strawberry.field
        def inspect_settings(self, settings: Settings) -> str:
            return f"{settings.mode}:{settings.retries}:{settings.flags}"

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        """
        query InspectSettings($settings: Settings!) {
          inspectSettings(settings: $settings)
        }
        """,
        variable_values={
            "settings": {"mode": "safe", "retries": None, "flags": [True, False]}
        },
    )

    assert not result.errors
    assert result.data == {"inspectSettings": "safe:None:[True, False]"}


def test_literal_validation_runs_inside_nested_lists() -> None:
    @strawberry.input
    class Settings:
        modes: list[Literal["fast", "safe"]]

    @strawberry.type
    class Query:
        @strawberry.field
        def inspect_settings(self, settings: Settings) -> str:
            return ",".join(settings.modes)

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        """
        query InspectSettings($settings: Settings!) {
          inspectSettings(settings: $settings)
        }
        """,
        variable_values={"settings": {"modes": ["fast", "invalid"]}},
    )

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == (
        "Expected value to be one of ('fast', 'safe'); received 'invalid'"
    )


def test_literal_values_must_have_the_same_type() -> None:
    @strawberry.type
    class Query:
        value: Literal[1, True]

    with pytest.raises(
        TypeError,
        match=r"Literal values must all have the same type; got \(1, True\)",
    ):
        strawberry.Schema(query=Query)


@pytest.mark.parametrize(
    "annotation",
    [Literal[1.0], Literal[b"value"], Literal[None]],  # noqa: PYI061
)
def test_unsupported_literal_types_are_rejected(annotation: object) -> None:
    class Query:
        __annotations__ = {"value": annotation}

    query_type = strawberry.type(Query)

    with pytest.raises(
        TypeError,
        match="only str, int, and bool values are supported",
    ):
        strawberry.Schema(query=query_type)


def test_empty_literal_is_rejected() -> None:
    @strawberry.type
    class Query:
        value: Literal[()]  # pyright: ignore[reportInvalidTypeForm]

    with pytest.raises(TypeError, match="Literal must contain at least one value"):
        strawberry.Schema(query=Query)


def test_literal_validation_distinguishes_booleans_and_integers() -> None:
    assert is_valid_literal_value(Literal[1], 1)
    assert not is_valid_literal_value(Literal[1], True)


def test_enum_literal_is_rejected() -> None:
    class Status(Enum):
        READY = "ready"

    @strawberry.type
    class Query:
        value: Literal[Status.READY]

    with pytest.raises(
        TypeError,
        match="only str, int, and bool values are supported",
    ):
        strawberry.Schema(query=Query)

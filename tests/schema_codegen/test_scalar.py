import textwrap

from strawberry.schema_codegen import codegen


def test_scalar():
    schema = """
    scalar LocalDate @specifiedBy(url: "https://scalars.graphql.org/andimarek/local-date.html")
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from strawberry.types.scalar import ScalarDefinition
        from typing import NewType

        LocalDate = NewType("LocalDate", object)

        scalar_map: dict[object, ScalarDefinition] = {LocalDate: strawberry.scalar(name="LocalDate", specified_by_url="https://scalars.graphql.org/andimarek/local-date.html", serialize=lambda v: v, parse_value=lambda v: v)}
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_scalar_with_description():
    schema = """
    "A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03."
    scalar LocalDate
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from strawberry.types.scalar import ScalarDefinition
        from typing import NewType

        LocalDate = NewType("LocalDate", object)

        scalar_map: dict[object, ScalarDefinition] = {LocalDate: strawberry.scalar(name="LocalDate", description="A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03.", serialize=lambda v: v, parse_value=lambda v: v)}
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_scalar_registered_via_scalar_map():
    schema = """
    scalar LocalDate @specifiedBy(url: "https://scalars.graphql.org/andimarek/local-date.html")

    type Query {
        when: LocalDate!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from strawberry.schema.config import StrawberryConfig
        from strawberry.types.scalar import ScalarDefinition
        from typing import NewType

        LocalDate = NewType("LocalDate", object)

        @strawberry.type
        class Query:
            when: LocalDate

        scalar_map: dict[object, ScalarDefinition] = {LocalDate: strawberry.scalar(name="LocalDate", specified_by_url="https://scalars.graphql.org/andimarek/local-date.html", serialize=lambda v: v, parse_value=lambda v: v)}

        schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_scalar_with_description_registered_via_scalar_map():
    schema = """
    "A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03."
    scalar LocalDate

    type Query {
        when: LocalDate!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from strawberry.schema.config import StrawberryConfig
        from strawberry.types.scalar import ScalarDefinition
        from typing import NewType

        LocalDate = NewType("LocalDate", object)

        @strawberry.type
        class Query:
            when: LocalDate

        scalar_map: dict[object, ScalarDefinition] = {LocalDate: strawberry.scalar(name="LocalDate", description="A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03.", serialize=lambda v: v, parse_value=lambda v: v)}

        schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_scalar_with_description_and_specified_by_registered_via_scalar_map():
    schema = """
    "A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03."
    scalar LocalDate @specifiedBy(url: "https://scalars.graphql.org/andimarek/local-date.html")

    type Query {
        when: LocalDate!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from strawberry.schema.config import StrawberryConfig
        from strawberry.types.scalar import ScalarDefinition
        from typing import NewType

        LocalDate = NewType("LocalDate", object)

        @strawberry.type
        class Query:
            when: LocalDate

        scalar_map: dict[object, ScalarDefinition] = {LocalDate: strawberry.scalar(name="LocalDate", description="A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03.", specified_by_url="https://scalars.graphql.org/andimarek/local-date.html", serialize=lambda v: v, parse_value=lambda v: v)}

        schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_jsonobject_scalar_without_override():
    """`JSONObject` is not a built-in — without a config it falls into the
    generic `scalar_map` path like any other unknown scalar."""
    schema = """
    scalar JSONObject

    type Query {
        data: JSONObject!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from strawberry.schema.config import StrawberryConfig
        from strawberry.types.scalar import ScalarDefinition
        from typing import NewType

        JSONObject = NewType("JSONObject", object)

        @strawberry.type
        class Query:
            data: JSONObject

        scalar_map: dict[object, ScalarDefinition] = {JSONObject: strawberry.scalar(name="JSONObject", serialize=lambda v: v, parse_value=lambda v: v)}

        schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_scalar_override_with_alias():
    """Mapping `JSONObject` to `strawberry.scalars:JSON` emits an aliased
    import and skips the `NewType` / `scalar_map` machinery."""
    schema = """
    scalar JSONObject

    type Query {
        data: JSONObject!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from strawberry.scalars import JSON as JSONObject

        @strawberry.type
        class Query:
            data: JSONObject

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    result = codegen(schema, scalar_overrides={"JSONObject": "strawberry.scalars:JSON"})
    assert result.strip() == expected


def test_scalar_override_same_name():
    """When the override target name matches the scalar name, no `as` alias
    is emitted."""
    schema = """
    scalar MyScalar

    type Query {
        a: MyScalar!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from my_app.scalars import MyScalar

        @strawberry.type
        class Query:
            a: MyScalar

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    result = codegen(schema, scalar_overrides={"MyScalar": "my_app.scalars:MyScalar"})
    assert result.strip() == expected


def test_scalar_override_wins_over_builtin():
    """Overrides apply to scalars that have built-in handling too — the
    built-in `from datetime import date` import is suppressed and the field
    annotation uses the scalar's GraphQL name (`Date`) rather than `date`."""
    schema = """
    scalar Date

    type Query {
        when: Date!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from my_app.scalars import UnixDate as Date

        @strawberry.type
        class Query:
            when: Date

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    result = codegen(schema, scalar_overrides={"Date": "my_app.scalars:UnixDate"})
    assert result.strip() == expected


def test_scalar_overrides_do_not_affect_other_scalars():
    """Overriding one scalar leaves the rest of the codegen unchanged."""
    schema = """
    scalar JSONObject
    scalar LocalDate

    type Query {
        a: JSONObject!
        b: LocalDate!
    }
    """

    result = codegen(schema, scalar_overrides={"JSONObject": "strawberry.scalars:JSON"})

    assert "from strawberry.scalars import JSON as JSONObject" in result
    assert 'LocalDate = NewType("LocalDate", object)' in result
    assert "scalar_map: dict[object, ScalarDefinition] = {LocalDate:" in result
    # No NewType for the overridden scalar.
    assert "JSONObject = NewType" not in result


def test_multiple_unknown_scalars_aggregated_into_scalar_map():
    schema = """
    scalar Foo
    scalar Bar

    type Query {
        a: Foo!
        b: Bar!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from strawberry.schema.config import StrawberryConfig
        from strawberry.types.scalar import ScalarDefinition
        from typing import NewType

        Foo = NewType("Foo", object)

        Bar = NewType("Bar", object)

        @strawberry.type
        class Query:
            a: Foo
            b: Bar

        scalar_map: dict[object, ScalarDefinition] = {Foo: strawberry.scalar(name="Foo", serialize=lambda v: v, parse_value=lambda v: v), Bar: strawberry.scalar(name="Bar", serialize=lambda v: v, parse_value=lambda v: v)}

        schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_builtin_scalars():
    schema = """
    scalar JSON
    scalar Date
    scalar Time
    scalar DateTime
    scalar UUID
    scalar Decimal

    type Example {
        a: JSON!
        b: Date!
        c: Time!
        d: DateTime!
        e: UUID!
        f: Decimal!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from datetime import date
        from datetime import datetime
        from datetime import time
        from decimal import Decimal
        from strawberry.scalars import JSON
        from uuid import UUID

        @strawberry.type
        class Example:
            a: JSON
            b: date
            c: time
            d: datetime
            e: UUID
            f: Decimal
        """
    ).strip()

    assert codegen(schema).strip() == expected

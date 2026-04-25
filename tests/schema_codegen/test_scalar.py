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
        from typing import NewType

        LocalDate = NewType("LocalDate", object)
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
        from typing import NewType

        LocalDate = NewType("LocalDate", object)
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
        from typing import NewType

        LocalDate = NewType("LocalDate", object)

        @strawberry.type
        class Query:
            when: LocalDate

        schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map={LocalDate: strawberry.scalar(name="LocalDate", specified_by_url="https://scalars.graphql.org/andimarek/local-date.html", serialize=lambda v: v, parse_value=lambda v: v)}))
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
        from typing import NewType

        LocalDate = NewType("LocalDate", object)

        @strawberry.type
        class Query:
            when: LocalDate

        schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map={LocalDate: strawberry.scalar(name="LocalDate", description="A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03.", serialize=lambda v: v, parse_value=lambda v: v)}))
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_jsonobject_scalar():
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

    assert codegen(schema).strip() == expected


def test_multiple_unknown_scalars_aggregated_into_scalar_map():
    schema = """
    scalar Foo
    scalar Bar

    type Query {
        a: Foo!
        b: Bar!
    }
    """

    output = codegen(schema)

    assert 'Foo = NewType("Foo", object)' in output
    assert 'Bar = NewType("Bar", object)' in output
    assert "from strawberry.schema.config import StrawberryConfig" in output
    assert "config=StrawberryConfig(scalar_map={" in output
    assert 'Foo: strawberry.scalar(name="Foo"' in output
    assert 'Bar: strawberry.scalar(name="Bar"' in output


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

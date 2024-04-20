import textwrap

from strawberry.schema_codegen import codegen


def test_scalar():
    schema = """
    scalar LocalDate @specifiedBy(url: "https://scalars.graphql.org/andimarek/local-date.html")
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from typing import NewType

        LocalDate = strawberry.scalar(NewType("LocalDate", object), specified_by_url="https://scalars.graphql.org/andimarek/local-date.html", serialize=lambda v: v, parse_value=lambda v: v)
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
        import strawberry
        from typing import NewType

        LocalDate = strawberry.scalar(NewType("LocalDate", object), description="A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03.", serialize=lambda v: v, parse_value=lambda v: v)
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
        import strawberry
        from datetime import date
        from datetime import datetime
        from datetime import time
        from decimal import Decimal
        from uuid import UUID

        @strawberry.type
        class Example:
            a: strawberry.JSON
            b: date
            c: time
            d: datetime
            e: UUID
            f: Decimal
        """
    ).strip()

    assert codegen(schema).strip() == expected

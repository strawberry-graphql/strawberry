import sys
import textwrap
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from uuid import UUID

import pytest

from strawberry.schema_codegen import codegen


def test_scalar():
    schema = """
    scalar LocalDate @specifiedBy(url: "https://scalars.graphql.org/andimarek/local-date.html")

    type Query {
        date: LocalDate
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
            date: LocalDate | None

        scalar_map: dict[object, ScalarDefinition] = {LocalDate: strawberry.scalar(name="LocalDate", specified_by_url="https://scalars.graphql.org/andimarek/local-date.html", serialize=lambda v: v, parse_value=lambda v: v)}

        schema = strawberry.Schema(query=Query, config=StrawberryConfig(scalar_map=scalar_map))
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_scalar_with_description():
    schema = """
    "A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03."
    scalar LocalDate

    type Query {
        date: LocalDate
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
            date: LocalDate | None

        scalar_map: dict[object, ScalarDefinition] = {LocalDate: strawberry.scalar(name="LocalDate", description="A date without a time-zone in the ISO-8601 calendar system, such as 2007-12-03.", serialize=lambda v: v, parse_value=lambda v: v)}

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


@pytest.mark.parametrize("federation", [False, True])
def test_generated_scalars_build_and_execute(tmp_path, monkeypatch, federation):
    prefix = (
        'extend schema @link(url: "https://specs.apollo.dev/federation/v2.7")'
        if federation
        else ""
    )
    source = codegen(
        prefix
        + """
        scalar JSON
        scalar UUID
        scalar Date
        "A domain value"
        scalar Foo @specifiedBy(url: "https://example.com/foo")
        scalar JSONObject
        type Query {
            data: JSON!
            custom: Foo!
            other: JSONObject!
            id: UUID!
            date: Date!
        }
        """
    )
    path = tmp_path / "generated_scalars.py"
    path.write_text(source)
    spec = spec_from_file_location("generated_scalars", path)
    module = module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "generated_scalars", module)
    spec.loader.exec_module(module)
    foo = module.schema._schema.get_type("Foo")
    assert foo.description == "A domain value"
    assert foo.specified_by_url == "https://example.com/foo"
    assert module.schema._schema.get_type("JSONObject").name == "JSONObject"
    result = module.schema.execute_sync(
        "{ data custom other }",
        root_value=module.Query(
            data={"value": 17},
            custom="custom",
            other=["other"],
            id=UUID(int=1),
            date=date(2026, 1, 2),
        ),
    )
    assert result.errors is None
    assert result.data == {
        "data": {"value": 17},
        "custom": "custom",
        "other": ["other"],
    }

import keyword
import textwrap

import pytest

from strawberry.schema_codegen import codegen


@pytest.mark.parametrize(
    "name",
    [keyword for keyword in keyword.kwlist if keyword not in ("False", "True", "None")],
)
def test_handles_keywords(name: str):
    schema = f"""
    type Example {{
        {name}: String!
    }}
    """

    expected = textwrap.dedent(
        f"""
        from __future__ import annotations
        import strawberry

        @strawberry.type
        class Example:
            {name}_: str = strawberry.field(name="{name}")
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_converts_names_to_snake_case():
    schema = """
    type Example {
        someField: String!
        allowCustomExportURL: Boolean!
        allowInsecureTLS: Boolean!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry

        @strawberry.type
        class Example:
            some_field: str
            allow_custom_export_url: bool = strawberry.field(name="allowCustomExportURL")
            allow_insecure_tls: bool = strawberry.field(name="allowInsecureTLS")
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_keeps_graphql_names_that_do_not_survive_camel_casing():
    # Strawberry camel-cases Python names to get the GraphQL name, so names that
    # are not reproduced by that conversion need an explicit alias.
    schema = """
    type Example {
        some_field: Int
        URL: String
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry

        @strawberry.type
        class Example:
            some_field: int | None = strawberry.field(name="some_field")
            url: str | None = strawberry.field(name="URL")
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_handles_names_converting_to_the_same_python_name():
    # `someField` and `some_field` both convert to `some_field`; the second one
    # must not overwrite the first.
    schema = """
    type Example {
        someField: String
        some_field: Int
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry

        @strawberry.type
        class Example:
            some_field: str | None
            some_field_: int | None = strawberry.field(name="some_field")
        """
    ).strip()

    assert codegen(schema).strip() == expected

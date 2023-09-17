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
        import strawberry

        @strawberry.type
        class Example:
            some_field: str
            allow_custom_export_url: bool
            allow_insecure_tls: bool
        """
    ).strip()

    assert codegen(schema).strip() == expected

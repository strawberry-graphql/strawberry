import textwrap
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


class _FakeSchema:
    pass


def test_django_export_schema():
    out = StringIO()
    call_command("export_schema", "tests.django.app.schema", stdout=out)
    output = out.getvalue()
    assert output

    expected = """\
    type Query {
      hello(name: String = null): String!
    }
    """
    assert output == textwrap.dedent(expected)


def test_django_export_schema_exception_handle():
    with pytest.raises(
        CommandError,
        match="No module named 'tests.django.app.fake_schema'",
    ):
        call_command("export_schema", "tests.django.app.fake_schema")

    mock_import_module = patch(
        "strawberry.django.management.commands.export_schema.import_module_symbol",
        return_value=_FakeSchema(),
    )
    with mock_import_module, pytest.raises(
        CommandError,
        match="The `schema` must be an instance of strawberry.Schema",
    ):
        call_command("export_schema", "tests.django.app.schema")

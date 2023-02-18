from io import StringIO
import textwrap

from django.core.management import call_command


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

"""Strawberry must stay importable when the optional pydantic extra isn't installed.

These tests run in a subprocess so that the modules imported by the rest of the
test suite don't leak in.
"""

import subprocess
import sys
import textwrap

import pytest


def _run(code: str, *, block_pydantic: bool) -> subprocess.CompletedProcess[str]:
    prelude = ""

    if block_pydantic:
        # A `None` entry in sys.modules makes `import pydantic` raise
        # ModuleNotFoundError, as if pydantic wasn't installed
        prelude = "import sys\nsys.modules['pydantic'] = None\n"

    return subprocess.run(
        [sys.executable, "-c", prelude + textwrap.dedent(code)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_strawberry_works_without_pydantic():
    result = _run(
        """
        import strawberry

        @strawberry.type
        class Query:
            @strawberry.field
            def hello(self) -> str:
                return "world"

        schema = strawberry.Schema(query=Query)
        print(schema.execute_sync("{ hello }").data)
        """,
        block_pydantic=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "{'hello': 'world'}"


def test_star_import_works_without_pydantic():
    result = _run("from strawberry import *", block_pydantic=True)

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "code",
    [
        "import strawberry\nstrawberry.pydantic",
        "import strawberry.pydantic",
        "from strawberry.pydantic import type",
    ],
)
def test_using_strawberry_pydantic_without_pydantic_explains_how_to_install_it(
    code: str,
):
    result = _run(code, block_pydantic=True)

    assert result.returncode != 0
    assert (
        "ModuleNotFoundError: strawberry.pydantic requires pydantic. "
        "Install it with `pip install 'strawberry-graphql[pydantic]'`."
    ) in result.stderr


def test_strawberry_pydantic_is_imported_on_first_access():
    result = _run(
        """
        import sys
        import strawberry

        assert "strawberry.pydantic" not in sys.modules

        strawberry.pydantic.type

        assert "strawberry.pydantic" in sys.modules
        """,
        block_pydantic=False,
    )

    assert result.returncode == 0, result.stderr


def test_using_strawberry_pydantic_with_an_old_pydantic_raises_an_error():
    result = _run(
        """
        import pydantic

        pydantic.VERSION = "2.10.6"

        import strawberry.pydantic
        """,
        block_pydantic=False,
    )

    assert result.returncode != 0
    assert (
        "ImportError: strawberry.pydantic requires pydantic>=2.11, but pydantic "
        "2.10.6 is installed. Upgrade it with `pip install -U 'pydantic>=2.11'`."
    ) in result.stderr

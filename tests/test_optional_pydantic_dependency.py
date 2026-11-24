"""Strawberry must stay importable when the optional pydantic extra isn't installed.

Importing strawberry also shouldn't import pydantic, which is slow to import,
until an app uses it.

These tests run in a subprocess so that the modules imported by the rest of the
test suite don't leak in.
"""

import pathlib
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
        # fails the test instead of hanging the test run
        timeout=60,
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


@pytest.mark.parametrize("code", ["import strawberry", "from strawberry import *"])
def test_importing_strawberry_does_not_import_pydantic(code: str):
    pytest.importorskip("pydantic")

    result = _run(
        f"""
        {code}
        import sys

        assert "pydantic" not in sys.modules
        """,
        block_pydantic=False,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "pydantic_init",
    [
        # like a pydantic installed for another Python version, or with a
        # pydantic-core that doesn't match it
        'raise ImportError("pydantic is broken")',
        # like a pydantic installed without its dependencies
        "import a_missing_pydantic_dependency",
    ],
)
def test_strawberry_works_with_a_broken_pydantic(
    tmp_path: pathlib.Path, pydantic_init: str
):
    (tmp_path / "pydantic").mkdir()
    (tmp_path / "pydantic" / "__init__.py").write_text(pydantic_init)

    result = _run(
        f"""
        import sys

        sys.path.insert(0, {str(tmp_path)!r})

        import strawberry
        from strawberry import *
        from strawberry.experimental import *

        assert "pydantic" not in globals()

        @strawberry.type
        class Query:
            @strawberry.field
            def hello(self) -> str:
                return "world"

        schema = strawberry.Schema(query=Query)
        print(schema.execute_sync("{{ hello }}").data)

        assert not hasattr(strawberry.experimental, "pydantic")
        """,
        block_pydantic=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "{'hello': 'world'}"


@pytest.mark.parametrize(
    "code",
    [
        "import strawberry.experimental.pydantic as module",
        "from strawberry.experimental import pydantic as module",
        "module = strawberry.experimental.pydantic",
    ],
)
def test_strawberry_experimental_pydantic_is_imported_on_first_access(code: str):
    pytest.importorskip("pydantic")

    result = _run(
        f"""
        import sys
        import strawberry

        assert "strawberry.experimental.pydantic" not in sys.modules

        {code}

        assert module is sys.modules["strawberry.experimental.pydantic"]
        assert module is strawberry.experimental.pydantic
        assert module.type is not None
        """,
        block_pydantic=False,
    )

    assert result.returncode == 0, result.stderr


def test_strawberry_experimental_star_import_includes_pydantic():
    pytest.importorskip("pydantic")

    result = _run(
        """
        import sys
        from strawberry.experimental import *

        assert pydantic is sys.modules["strawberry.experimental.pydantic"]
        """,
        block_pydantic=False,
    )

    assert result.returncode == 0, result.stderr


def test_strawberry_experimental_has_no_pydantic_attribute_without_pydantic():
    result = _run(
        """
        import strawberry

        assert not hasattr(strawberry.experimental, "pydantic")
        assert getattr(strawberry.experimental, "pydantic", None) is None

        from strawberry.experimental import *

        assert "pydantic" not in globals()
        """,
        block_pydantic=True,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("code", "exception"),
    [
        ("import strawberry\nstrawberry.experimental.pydantic", "AttributeError"),
        ("import strawberry.experimental.pydantic", "ModuleNotFoundError"),
        ("from strawberry.experimental import pydantic", "ModuleNotFoundError"),
    ],
)
def test_using_strawberry_experimental_pydantic_without_pydantic_raises_an_error(
    code: str, exception: str
):
    result = _run(code, block_pydantic=True)

    assert result.returncode != 0
    # the message of the ModuleNotFoundError raised by `import pydantic`, see `_run`
    assert f"{exception}: import of pydantic halted" in result.stderr


_PYDANTIC_ERROR_EXTENSION_SCHEMA = """
import sys

import strawberry
from strawberry.extensions import PydanticErrorExtension

@strawberry.type
class Query:
    @strawberry.field
    def fail(self) -> str:
        raise ValueError("failed")

    @strawberry.field
    def validate(self) -> int:
        import pydantic

        class User(pydantic.BaseModel):
            age: int

        return User(age="not a number").age

schema = strawberry.Schema(query=Query, extensions=[PydanticErrorExtension])
"""


def test_pydantic_error_extension_works_without_pydantic():
    result = _run(
        _PYDANTIC_ERROR_EXTENSION_SCHEMA
        + """
result = schema.execute_sync("{ fail }")

assert result.errors[0].message == "failed"
assert not result.errors[0].extensions
""",
        block_pydantic=True,
    )

    assert result.returncode == 0, result.stderr


def test_pydantic_error_extension_formats_errors_once_pydantic_is_used():
    pytest.importorskip("pydantic")

    result = _run(
        _PYDANTIC_ERROR_EXTENSION_SCHEMA
        + """
result = schema.execute_sync("{ fail }")

assert not result.errors[0].extensions
assert "pydantic" not in sys.modules

result = schema.execute_sync("{ validate }")

print(result.errors[0].extensions["validation_errors"][0]["field"])
""",
        block_pydantic=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "age"


def test_pydantic_error_extension_waits_for_pydantic_imported_by_another_thread(
    tmp_path: pathlib.Path,
):
    # a pydantic whose import blocks halfway, before it defines ValidationError,
    # until the test lets it finish
    (tmp_path / "pydantic").mkdir()
    (tmp_path / "pydantic" / "__init__.py").write_text(
        textwrap.dedent(
            """
            import sys

            test = sys.modules["__main__"]
            test.pydantic_import_started.set()
            assert test.finish_pydantic_import.wait(timeout=10)

            class ValidationError(Exception):
                pass
            """
        )
    )

    result = _run(
        f"""
        import sys
        import threading

        sys.path.insert(0, {str(tmp_path)!r})

        import strawberry
        from strawberry.extensions import PydanticErrorExtension

        @strawberry.type
        class Query:
            hello: str = "world"

            @strawberry.field
            def fail(self) -> str | None:
                raise ValueError("failed")

        schema = strawberry.Schema(query=Query, extensions=[PydanticErrorExtension])

        pydantic_import_started = threading.Event()
        finish_pydantic_import = threading.Event()

        importer = threading.Thread(target=lambda: __import__("pydantic"))
        importer.start()
        assert pydantic_import_started.wait(timeout=10)

        results = []
        operation = threading.Thread(
            target=lambda: results.append(
                schema.execute_sync("{{ hello fail }}", root_value=Query())
            )
        )
        operation.start()
        # gives the operation time to finish while pydantic is still importing
        operation.join(timeout=0.2)
        finish_pydantic_import.set()
        operation.join(timeout=10)
        importer.join(timeout=10)

        (result,) = results
        print(result.data, [error.message for error in result.errors])
        """,
        block_pydantic=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "{'hello': 'world', 'fail': None} ['failed']"


@pytest.mark.parametrize(
    ("code", "exception"),
    [
        ("import strawberry\nstrawberry.pydantic", "AttributeError"),
        ("import strawberry.pydantic", "ModuleNotFoundError"),
        ("from strawberry.pydantic import type", "ModuleNotFoundError"),
    ],
)
def test_using_strawberry_pydantic_without_pydantic_explains_how_to_install_it(
    code: str, exception: str
):
    result = _run(code, block_pydantic=True)

    assert result.returncode != 0
    assert (
        f"{exception}: strawberry.pydantic requires pydantic. "
        "Install it with `pip install 'strawberry-graphql[pydantic]'`."
    ) in result.stderr


def test_strawberry_has_no_pydantic_attribute_without_pydantic():
    result = _run(
        """
        import strawberry

        assert not hasattr(strawberry, "pydantic")
        assert getattr(strawberry, "pydantic", None) is None
        """,
        block_pydantic=True,
    )

    assert result.returncode == 0, result.stderr


def test_strawberry_pydantic_is_imported_on_first_access():
    pytest.importorskip("pydantic", minversion="2.11")

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
    pytest.importorskip("pydantic")

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

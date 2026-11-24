import importlib
import sys
import textwrap
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

import pytest

import strawberry
from strawberry.types.lazy_type import LazyType

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 15), reason="Native lazy imports require Python 3.15+"
)


@pytest.fixture(
    params=[
        "lazy from {module} import {names}\n",
        '__lazy_modules__ = ["{module}"]\nfrom {module} import {names}\n',
    ],
    ids=["lazy-from", "lazy-modules"],
)
def lazy_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Iterator[types.ModuleType]:
    package_name = "native_lazy_types"
    package_path = tmp_path / package_name
    package_path.mkdir()

    (package_path / "models.py").write_text(
        textwrap.dedent(
            """\
            import strawberry

            @strawberry.type
            class User:
                name: str
            """
        )
    )
    (package_path / "exports.py").write_text(
        request.param.format(module=f"{package_name}.models", names="User, Missing")
    )
    (package_path / "__init__.py").write_text(
        request.param.format(
            module=f"{package_name}.exports", names="User as ExportedUser, Missing"
        )
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    try:
        module = importlib.import_module(package_name)

        assert type(module.__dict__["ExportedUser"]) is types.LazyImportType
        assert f"{package_name}.exports" not in sys.modules
        assert f"{package_name}.models" not in sys.modules

        yield module
    finally:
        for name in (package_name, f"{package_name}.exports", f"{package_name}.models"):
            sys.modules.pop(name, None)


@pytest.mark.parametrize(
    ("module", "package"), [("native_lazy_types", None), (".", "native_lazy_types")]
)
def test_resolve_native_lazy_reexports(lazy_package, module, package):
    lazy_type = LazyType("ExportedUser", module, package)

    resolved = lazy_type.resolve_type()

    assert "native_lazy_types.models" in sys.modules
    assert resolved is sys.modules["native_lazy_types.models"].User
    assert lazy_type.resolve_type() is resolved
    assert lazy_package.__dict__["ExportedUser"] is resolved
    assert type(lazy_package.__dict__["Missing"]) is types.LazyImportType


async def test_schema_with_native_lazy_reexports(lazy_package):
    @strawberry.type
    class Query:
        user: Annotated["ExportedUser", strawberry.lazy("native_lazy_types")]  # noqa: F821

    assert "native_lazy_types.models" not in sys.modules

    schema = strawberry.Schema(query=Query)
    root = Query(user=lazy_package.ExportedUser(name="Ada"))

    result = schema.execute_sync("{ user { name } }", root_value=root)

    assert result.errors is None
    assert result.data == {"user": {"name": "Ada"}}

    async_result = await schema.execute("{ user { name } }", root_value=root)

    assert async_result.errors is None
    assert async_result.data == {"user": {"name": "Ada"}}
    assert type(lazy_package.__dict__["Missing"]) is types.LazyImportType


def test_native_lazy_import_errors_propagate(lazy_package):
    lazy_type = LazyType("Missing", lazy_package.__name__)

    with pytest.raises(ImportError, match="cannot import name 'Missing'"):
        lazy_type.resolve_type()


def test_native_lazy_import_attribute_errors_propagate(lazy_package):
    models_path = Path(lazy_package.__file__).with_name("models.py")
    models_path.write_text('raise AttributeError("module initialization failed")\n')

    lazy_type = LazyType("ExportedUser", lazy_package.__name__)

    with pytest.raises(AttributeError, match="module initialization failed"):
        lazy_type.resolve_type()

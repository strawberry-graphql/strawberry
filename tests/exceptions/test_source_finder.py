"""Tests for finding the source of functions and classes in modules without `__file__`.

`__file__` is optional on modules: it isn't set for code run with `python -c` or
in the REPL, and some CPython versions (3.13.15+, 3.14.7+ and 3.15) remove it
from `__main__` before an uncaught exception from a script reaches
`sys.excepthook`.
"""

import importlib.machinery
import importlib.util
import sys
import textwrap
import types
from pathlib import Path

import pytest

from strawberry.exceptions.exception_source import ExceptionSource
from strawberry.exceptions.utils.source_finder import SourceFinder

pytest.importorskip("libcst")

SOURCE = textwrap.dedent(
    """
    def hello(self):
        return "hi"


    class Query:
        name: str
    """
)


def _make_module(
    monkeypatch: pytest.MonkeyPatch,
    path: Path,
    *,
    name: str = "__main__",
    loader: object = None,
    spec: importlib.machinery.ModuleSpec | None = None,
) -> types.ModuleType:
    """Create a module from `path` without `__file__` and add it to sys.modules."""
    path.write_text(SOURCE, encoding="utf-8")

    module = types.ModuleType(name)
    module.__loader__ = loader
    module.__spec__ = spec

    exec(compile(SOURCE, str(path), "exec"), module.__dict__)  # noqa: S102

    assert not hasattr(module, "__file__")

    monkeypatch.setitem(sys.modules, name, module)

    return module


def _find_function(module: types.ModuleType) -> ExceptionSource | None:
    return SourceFinder().find_function_from_object(module.hello)


def test_finds_source_using_the_loader_when_module_has_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # this is what `__main__` looks like when an uncaught exception from a
    # script reaches `sys.excepthook` on Python 3.13.15+ and 3.14.7+
    path = tmp_path / "app.py"
    loader = importlib.machinery.SourceFileLoader("__main__", str(path))
    module = _make_module(monkeypatch, path, loader=loader)

    source = _find_function(module)

    assert source is not None
    assert source.path == path
    assert source.code == SOURCE
    assert source.error_line == 2


def test_finds_class_source_using_the_loader_when_module_has_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "app.py"
    loader = importlib.machinery.SourceFileLoader("__main__", str(path))
    module = _make_module(monkeypatch, path, loader=loader)

    source = SourceFinder().find_class_from_object(module.Query)

    assert source is not None
    assert source.path == path
    assert source.error_line == 6


def test_finds_source_using_the_spec_when_module_has_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "app.py"
    spec = importlib.util.spec_from_file_location("app", path)
    module = _make_module(monkeypatch, path, name="app", spec=spec)

    source = _find_function(module)

    assert source is not None
    assert source.path == path


def test_returns_none_when_module_has_no_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # like `__main__` when running `python -c` or the REPL
    module = _make_module(monkeypatch, tmp_path / "app.py")

    assert _find_function(module) is None


def test_returns_none_when_loader_cannot_return_a_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "app.py"
    # SourceFileLoader.get_filename raises ImportError for other module names
    loader = importlib.machinery.SourceFileLoader("other", str(path))
    module = _make_module(monkeypatch, path, loader=loader)

    assert _find_function(module) is None


def test_returns_none_when_source_file_does_not_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "app.py"
    loader = importlib.machinery.SourceFileLoader("__main__", str(path))
    module = _make_module(monkeypatch, path, loader=loader)

    path.unlink()

    assert _find_function(module) is None


def test_returns_none_for_module_not_in_sys_modules():
    def hello(): ...

    hello.__module__ = "strawberry_missing_package.missing_module"

    assert SourceFinder().find_function_from_object(hello) is None


@pytest.mark.parametrize("filename", ["<string>", "<stdin>"])
def test_returns_none_for_union_call_without_a_source_file(filename: str):
    source = SourceFinder().find_union_call(Path(filename), "Union", int)

    assert source is None

from pathlib import Path

from inline_snapshot import snapshot

from strawberry.utils.importer import import_module_symbol
from strawberry.utils.locate_definition import locate_definition
from tests.typecheckers.utils.marks import skip_on_windows

pytestmark = skip_on_windows


def _simplify_path(path: str) -> str:
    path = Path(path)

    root = Path(__file__).parents[1]

    return str(path.relative_to(root))


def test_find_model_name() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "User")

    assert _simplify_path(result) == snapshot(
        "fixtures/sample_package/sample_module.py:38:7"
    )


def test_find_model_name_enum() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "Role")

    assert _simplify_path(result) == snapshot(
        "fixtures/sample_package/sample_module.py:32:7"
    )


def test_find_model_name_scalar() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "ExampleScalar")

    assert _simplify_path(result) == snapshot(
        "fixtures/sample_package/sample_module.py:7:13"
    )


def test_find_model_field() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "User.name")

    assert _simplify_path(result) == snapshot(
        "fixtures/sample_package/sample_module.py:39:5"
    )


def test_find_model_field_scalar() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "User.example_scalar")

    assert _simplify_path(result) == snapshot(
        "fixtures/sample_package/sample_module.py:42:5"
    )


def test_find_model_field_with_resolver() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "Query.user")

    assert _simplify_path(result) == snapshot(
        "fixtures/sample_package/sample_module.py:50:5"
    )


def test_find_missing_model() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "Missing")

    assert result is None


def test_find_missing_model_field() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "Missing.field")

    assert result is None


def test_find_union() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "UnionExample")

    assert _simplify_path(result) == snapshot(
        "fixtures/sample_package/sample_module.py:23:16"
    )


def test_find_inline_union() -> None:
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "InlineUnion")

    assert _simplify_path(result) == snapshot(
        "fixtures/sample_package/sample_module.py:44:19"
    )

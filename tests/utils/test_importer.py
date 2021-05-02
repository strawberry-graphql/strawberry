import pytest

from strawberry.utils.importer import import_module_symbol
from tests.fixtures.sample_package.sample_module import sample_instance, schema


def test_symbol_import():
    selector = "tests.fixtures.sample_package.sample_module:schema"
    schema_symbol = import_module_symbol(selector)
    assert schema_symbol == schema


def test_default_symbol_import():
    selector = "tests.fixtures.sample_package.sample_module"
    schema_symbol = import_module_symbol(selector, default_symbol_name="schema")
    assert schema_symbol == schema


def test_nested_symbol_import():
    selector = "tests.fixtures.sample_package.sample_module:sample_instance.schema"
    schema_symbol = import_module_symbol(selector)
    assert schema_symbol == sample_instance.schema


def test_not_specifying_a_symbol():
    selector = "tests.fixtures.sample_package.sample_module"
    with pytest.raises(ValueError) as exc:
        import_module_symbol(selector)
    assert "Selector does not include a symbol name" in str(exc.value)


def test_invalid_module_import():
    selector = "not.existing.module:schema"
    with pytest.raises(ImportError):
        import_module_symbol(selector)


def test_invalid_symbol_import():
    selector = "tests.fixtures.sample_package.sample_module:not.existing.symbol"
    with pytest.raises(AttributeError):
        import_module_symbol(selector)

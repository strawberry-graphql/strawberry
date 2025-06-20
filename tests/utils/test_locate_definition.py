from strawberry.utils.importer import import_module_symbol
from strawberry.utils.locate_definition import locate_definition


def test_find_model_name(mocker):
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "User")

    assert result.endswith("tests/fixtures/sample_package/sample_module.py:18:7")


def test_find_model_name_enum(mocker):
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "Role")

    assert result.endswith("tests/fixtures/sample_package/sample_module.py:12:7")


def test_find_model_field(mocker):
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "User.name")

    assert result.endswith("tests/fixtures/sample_package/sample_module.py:19:5")


def test_find_model_field_with_resolver(mocker):
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "Query.user")

    assert result.endswith("tests/fixtures/sample_package/sample_module.py:27:5")


def test_find_missing_model(mocker):
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "Missing")

    assert result is None


def test_find_missing_model_field(mocker):
    schema = import_module_symbol(
        "tests.fixtures.sample_package.sample_module", default_symbol_name="schema"
    )
    result = locate_definition(schema, "Missing.field")

    assert result is None

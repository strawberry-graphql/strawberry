from strawberry.cli.commands.export_schema import export_schema as cmd_export_schema


def test_schema_export(cli_runner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cmd_export_schema, [selector])

    assert result.exit_code == 0
    assert result.output == (
        "type Query {\n"
        "  user: User!\n"
        "}\n"
        "\n"
        "type User {\n"
        "  name: String!\n"
        "  age: Int!\n"
        "}\n"
    )


def test_default_schema_symbol_name(cli_runner):
    selector = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cmd_export_schema, [selector])

    assert result.exit_code == 0


def test_app_dir_option(cli_runner):
    selector = "sample_module"
    result = cli_runner.invoke(
        cmd_export_schema, ["--app-dir=./tests/fixtures/sample_package", selector]
    )

    assert result.exit_code == 0


def test_invalid_module(cli_runner):
    selector = "not.existing.module"
    result = cli_runner.invoke(cmd_export_schema, [selector])

    expected_error = "Error: No module named 'not'"

    assert result.exit_code == 2
    assert expected_error in result.output


def test_invalid_symbol(cli_runner):
    selector = "tests.fixtures.sample_package.sample_module:not.existing.symbol"
    result = cli_runner.invoke(cmd_export_schema, [selector])

    expected_error = (
        "Error: module 'tests.fixtures.sample_package.sample_module' "
        "has no attribute 'not'"
    )

    assert result.exit_code == 2
    assert expected_error in result.output


def test_invalid_schema_instance(cli_runner):
    selector = "tests.fixtures.sample_package.sample_module:not_a_schema"
    result = cli_runner.invoke(cmd_export_schema, [selector])

    expected_error = "Error: The `schema` must be an instance of strawberry.Schema"

    assert result.exit_code == 2
    assert expected_error in result.output

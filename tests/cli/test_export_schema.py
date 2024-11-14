from typer import Typer
from typer.testing import CliRunner


def test_schema_export(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(cli_app, ["export-schema", selector])

    assert result.exit_code == 0
    assert result.stdout == (
        "type Query {\n"
        "  user: User!\n"
        "}\n"
        "\n"
        "type User {\n"
        "  name: String!\n"
        "  age: Int!\n"
        "}\n"
    )


def test_schema_export_with_federation_version_override(
    cli_app: Typer, cli_runner: CliRunner
):
    selector = "tests.fixtures.sample_package.sample_module_federated:schema"
    result = cli_runner.invoke(
        cli_app, ["export-schema", selector, "--federation-version=2.5"]
    )
    assert result.exit_code == 0
    assert result.stdout == (
        'schema @link(url: "https://specs.apollo.dev/federation/v2.5", import: '
        '["@key"]) {\n'
        "  query: Query\n"
        "}\n"
        "\n"
        'type Organization @key(fields: "id") {\n'
        "  id: ID!\n"
        "  name: String!\n"
        "  owner: User!\n"
        "}\n"
        "\n"
        "type Query {\n"
        "  _entities(representations: [_Any!]!): [_Entity]!\n"
        "  _service: _Service!\n"
        "  organizations: [Organization!]!\n"
        "  organization(id: ID!): Organization\n"
        "}\n"
        "\n"
        'type User @key(fields: "id", resolvable: false) {\n'
        "  id: ID!\n"
        "}\n"
        "\n"
        "scalar _Any\n"
        "\n"
        "union _Entity = Organization | User\n"
        "\n"
        "type _Service {\n"
        "  sdl: String!\n"
        "}\n"
    )


def test_default_schema_symbol_name(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module"
    result = cli_runner.invoke(cli_app, ["export-schema", selector])

    assert result.exit_code == 0


def test_app_dir_option(cli_app: Typer, cli_runner: CliRunner):
    selector = "sample_module"
    result = cli_runner.invoke(
        cli_app,
        ["export-schema", "--app-dir=./tests/fixtures/sample_package", selector],
    )

    assert result.exit_code == 0


def test_invalid_module(cli_app: Typer, cli_runner: CliRunner):
    selector = "not.existing.module"
    result = cli_runner.invoke(cli_app, ["export-schema", selector])

    expected_error = "Error: No module named 'not'"

    assert result.exit_code == 2
    assert expected_error in result.stdout.replace("\n", "")


def test_invalid_symbol(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:not.existing.symbol"
    result = cli_runner.invoke(cli_app, ["export-schema", selector])

    expected_error = (
        "Error: module 'tests.fixtures.sample_package.sample_module' "
        "has no attribute 'not'"
    )

    assert result.exit_code == 2
    assert expected_error in result.stdout.replace("\n", "")


def test_invalid_schema_instance(cli_app: Typer, cli_runner: CliRunner):
    selector = "tests.fixtures.sample_package.sample_module:not_a_schema"
    result = cli_runner.invoke(cli_app, ["export-schema", selector])

    expected_error = "Error: The `schema` must be an instance of strawberry.Schema"

    assert result.exit_code == 2
    assert expected_error in result.stdout.replace("\n", "")


def test_output_option(cli_app: Typer, cli_runner: CliRunner, tmp_path):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    output = tmp_path / "schema.graphql"
    output_commands = ["--output", "-o"]
    for output_command in output_commands:
        result = cli_runner.invoke(
            cli_app, ["export-schema", selector, output_command, str(output)]
        )

        assert result.exit_code == 0
        assert output.read_text() == (
            "type Query {\n"
            "  user: User!\n"
            "}\n"
            "\n"
            "type User {\n"
            "  name: String!\n"
            "  age: Int!\n"
            "}"
        )

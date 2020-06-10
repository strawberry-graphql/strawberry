import os

from click.testing import CliRunner

from strawberry.cli.commands.import_schema import import_schema as cmd_import_schema

SPECIFIC_TYPE = "Film.gql"
SPECIFIC_SCHEMA = "swapi_schema.gql"


def test_cli_cmd_import_schema(mocker):

    runner = CliRunner()
    file = os.path.join(os.getcwd(), "tests", "cli", "helpers", SPECIFIC_SCHEMA)
    result = runner.invoke(cmd_import_schema, [file], "-R")
    assert result.exit_code == 0


def test_cli_cmd_import_specific_object_type(mocker):

    runner = CliRunner()
    file = os.path.join(os.getcwd(), "tests", "cli", "helpers", "type", SPECIFIC_TYPE)
    output = os.path.join(".", "tests", "cli", "helpers", "output")
    result = runner.invoke(cmd_import_schema, [file, "--output", output])
    assert result.exit_code == 0

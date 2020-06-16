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
    result = runner.invoke(cmd_import_schema, [file])
    cwd = os.getcwd()
    # Just so it's easier to read the result it is in the .gitignore file
    with open(
        os.path.join(cwd, "tests", "cli", "output", "test_import_schema.py"), "w"
    ) as f:
        f.write(result.output)
    assert result.exit_code == 0

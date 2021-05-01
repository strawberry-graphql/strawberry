from click.testing import CliRunner

from strawberry.cli.commands.export_schema import export_schema as cmd_export_schema


def test_cli_cmd_export_schema():
    cli_runner = CliRunner()
    result = cli_runner.invoke(
        cmd_export_schema, ["tests.cli.helpers.sample_schema:schema"]
    )
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

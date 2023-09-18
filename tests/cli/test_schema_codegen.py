from pathlib import Path

import pytest
from typer import Typer
from typer.testing import CliRunner

schema = """
type Query {
    hello: String!
}
"""

expected_output = """
import strawberry

@strawberry.type
class Query:
    hello: str

schema = strawberry.Schema(query=Query)
""".strip()


@pytest.fixture
def schema_file(tmp_path: Path) -> Path:
    schema_file = tmp_path / "schema.graphql"
    schema_file.write_text(schema)
    return schema_file


def test_schema_codegen(cli_app: Typer, cli_runner: CliRunner, schema_file: Path):
    result = cli_runner.invoke(cli_app, ["schema-codegen", str(schema_file)])

    assert result.exit_code == 0
    assert result.stdout.strip() == expected_output


def test_schema_codegen_to_file(
    cli_app: Typer, cli_runner: CliRunner, schema_file: Path, tmp_path: Path
):
    output_file = tmp_path / "schema.py"

    result = cli_runner.invoke(
        cli_app, ["schema-codegen", str(schema_file), "--output", str(output_file)]
    )

    assert "Code generated at `schema.py`" in result.stdout.strip()
    assert result.exit_code == 0
    assert output_file.read_text().strip() == expected_output


def test_overrides_file_if_exists(
    cli_app: Typer, cli_runner: CliRunner, schema_file: Path, tmp_path: Path
):
    output_file = tmp_path / "schema.py"
    output_file.write_text("old content")

    result = cli_runner.invoke(
        cli_app, ["schema-codegen", str(schema_file), "--output", str(output_file)]
    )

    assert "Code generated at `schema.py`" in result.stdout.strip()
    assert result.exit_code == 0
    assert output_file.read_text().strip() == expected_output

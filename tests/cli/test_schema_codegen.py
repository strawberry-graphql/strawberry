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
from __future__ import annotations
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


def test_schema_codegen_with_config(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
):
    schema_file = tmp_path / "schema.graphql"
    schema_file.write_text(
        "scalar JSONObject\n\ntype Query {\n  data: JSONObject!\n}\n"
    )

    config_file = tmp_path / "codegen.yaml"
    config_file.write_text("scalars:\n  JSONObject: strawberry.scalars:JSON\n")

    result = cli_runner.invoke(
        cli_app,
        ["schema-codegen", str(schema_file), "-c", str(config_file)],
    )

    assert result.exit_code == 0, result.stdout
    assert "from strawberry.scalars import JSON as JSONObject" in result.stdout
    assert "NewType" not in result.stdout
    assert "scalar_map" not in result.stdout


def test_schema_codegen_config_malformed(
    cli_app: Typer, cli_runner: CliRunner, schema_file: Path, tmp_path: Path
):
    config_file = tmp_path / "codegen.yaml"
    # Value missing `:` separator — invalid `<module>:<object>` shape.
    config_file.write_text("scalars:\n  JSONObject: strawberry.scalars.JSON\n")

    result = cli_runner.invoke(
        cli_app,
        ["schema-codegen", str(schema_file), "--config", str(config_file)],
    )

    assert result.exit_code != 0
    assert "JSONObject" in result.output
    assert "<module>:<object>" in result.output

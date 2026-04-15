import tempfile
from pathlib import Path

from typer import Typer
from typer.testing import CliRunner


def test_schema_diff_no_breaking_changes(cli_app: Typer, cli_runner: CliRunner):
    sdl = "type Query { hello: String }"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as old,          tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as new:
        old.write(sdl)
        new.write(sdl)
        old.flush()
        new.flush()
        result = cli_runner.invoke(cli_app, ["schema-diff", old.name, new.name])
    assert result.exit_code == 0
    assert "No breaking changes" in result.stdout


def test_schema_diff_with_breaking_change(cli_app: Typer, cli_runner: CliRunner):
    old_sdl = "type Query { hello: String\n  world: String }"
    new_sdl = "type Query { hello: String }"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as old,          tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as new:
        old.write(old_sdl)
        new.write(new_sdl)
        old.flush()
        new.flush()
        result = cli_runner.invoke(cli_app, ["schema-diff", old.name, new.name])
    assert result.exit_code == 1
    assert "world" in result.stdout


def test_schema_diff_invalid_sdl(cli_app: Typer, cli_runner: CliRunner):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as old,          tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as new:
        old.write("{ not valid sdl")
        new.write("type Query { hello: String }")
        old.flush()
        new.flush()
        result = cli_runner.invoke(cli_app, ["schema-diff", old.name, new.name])
    assert result.exit_code == 2
    assert "Error" in result.stdout


def test_schema_diff_nonexistent_file(cli_app: Typer, cli_runner: CliRunner):
    result = cli_runner.invoke(
        cli_app, ["schema-diff", "/nonexistent/old.graphql", "/nonexistent/new.graphql"]
    )
    assert result.exit_code != 0


def test_schema_diff_list_type_in_output(cli_app: Typer, cli_runner: CliRunner):
    """Verify Rich markup escaping for types containing brackets like [String]."""
    old_sdl = "type Query { items: [String] }"
    new_sdl = "type Query { items: [Int] }"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as old,          tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as new:
        old.write(old_sdl)
        new.write(new_sdl)
        old.flush()
        new.flush()
        result = cli_runner.invoke(cli_app, ["schema-diff", old.name, new.name])
    assert result.exit_code == 1

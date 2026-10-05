from __future__ import annotations

from pathlib import Path

from typer import Typer
from typer.testing import CliRunner


def _write_sdl(path: Path, content: str) -> Path:
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def test_breaking_changes_no_breaking_changes(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
) -> None:
    sdl = """
    type Query {
      hello: String
    }
    """
    old = _write_sdl(tmp_path / "old.graphql", sdl)
    new = _write_sdl(tmp_path / "new.graphql", sdl)

    result = cli_runner.invoke(cli_app, ["breaking-changes", str(old), str(new)])

    assert result.exit_code == 0
    assert "No breaking changes found." in result.stdout


def test_breaking_changes_field_removed_exit_1(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
) -> None:
    old = _write_sdl(
        tmp_path / "old.graphql",
        """
        type Query {
          hello: String
          world: String
        }
        """,
    )
    new = _write_sdl(
        tmp_path / "new.graphql",
        """
        type Query {
          hello: String
        }
        """,
    )

    result = cli_runner.invoke(cli_app, ["breaking-changes", str(old), str(new)])

    assert result.exit_code == 1
    # field removal is a breaking change; description text is printed
    assert "world" in result.stdout


def test_breaking_changes_list_type_description_does_not_crash_rich(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
) -> None:
    """List types use [String!] notation; must not crash Rich markup parsing."""
    old = _write_sdl(
        tmp_path / "old.graphql",
        """
        type Query {
          tags: [String!]!
        }
        """,
    )
    new = _write_sdl(
        tmp_path / "new.graphql",
        """
        type Query {
          tags: String
        }
        """,
    )

    result = cli_runner.invoke(cli_app, ["breaking-changes", str(old), str(new)])

    assert result.exit_code == 1
    # Should print a type-change description without MarkupError traceback
    assert "Error" not in result.stdout or "MarkupError" not in (
        result.stdout + (result.stderr or "")
    )
    assert "tags" in result.stdout
    assert (
        result.exception is None
        or not isinstance(result.exception, Exception)
        or "MarkupError" not in type(result.exception).__name__
    )


def test_breaking_changes_invalid_sdl_exit_2(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
) -> None:
    old = _write_sdl(tmp_path / "old.graphql", "type Query { hello: String }")
    new = _write_sdl(tmp_path / "new.graphql", "{ not valid")

    result = cli_runner.invoke(cli_app, ["breaking-changes", str(old), str(new)])

    assert result.exit_code == 2
    assert "Error" in result.stdout


def test_breaking_changes_missing_file_exit_2(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
) -> None:
    old = tmp_path / "missing-old.graphql"
    new = _write_sdl(tmp_path / "new.graphql", "type Query { hello: String }")

    result = cli_runner.invoke(cli_app, ["breaking-changes", str(old), str(new)])

    # Typer validates exists=True on Path args before our handler
    assert result.exit_code != 0

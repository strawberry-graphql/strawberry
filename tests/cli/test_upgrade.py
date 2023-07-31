from pathlib import Path

from pytest_snapshot.plugin import Snapshot
from typer import Typer
from typer.testing import CliRunner

HERE = Path(__file__).parent


def test_upgrade_returns_error_code_if_codemod_does_not_exist(
    cli_app: Typer, cli_runner: CliRunner
):
    result = cli_runner.invoke(
        cli_app,
        ["upgrade", "a_random_codemod", "."],
    )

    assert result.exit_code == 2
    assert 'Upgrade named "a_random_codemod" does not exist' in result.stdout


def test_upgrade_works_annotated_unions(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path, snapshot: Snapshot
):
    source = HERE / "fixtures/unions.py"

    target = tmp_path / "unions.py"
    target.write_text(source.read_text())

    result = cli_runner.invoke(
        cli_app,
        ["upgrade", "--python-target", "3.11", "annotated-union", str(target)],
    )

    assert result.exit_code == 1
    assert "1 files changed\n  - 0 files skipped" in result.stdout

    snapshot.snapshot_dir = HERE / "snapshots"
    snapshot.assert_match(target.read_text(), "unions.py")


def test_upgrade_works_annotated_unions_target_python(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path, snapshot: Snapshot
):
    source = HERE / "fixtures/unions.py"

    target = tmp_path / "unions.py"
    target.write_text(source.read_text())

    result = cli_runner.invoke(
        cli_app,
        ["upgrade", "--python-target", "3.8", "annotated-union", str(target)],
    )

    assert result.exit_code == 1
    assert "1 files changed\n  - 0 files skipped" in result.stdout

    snapshot.snapshot_dir = HERE / "snapshots"
    snapshot.assert_match(target.read_text(), "unions_py38.py")


def test_upgrade_works_annotated_unions_typing_extensions(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path, snapshot: Snapshot
):
    source = HERE / "fixtures/unions.py"

    target = tmp_path / "unions.py"
    target.write_text(source.read_text())

    result = cli_runner.invoke(
        cli_app,
        [
            "upgrade",
            "--use-typing-extensions",
            "--python-target",
            "3.11",
            "annotated-union",
            str(target),
        ],
    )

    assert result.exit_code == 1
    assert "1 files changed\n  - 0 files skipped" in result.stdout

    snapshot.snapshot_dir = HERE / "snapshots"
    snapshot.assert_match(target.read_text(), "unions_typing_extension.py")

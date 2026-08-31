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


def test_upgrade_works_schema_extension_info(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
) -> None:
    target = tmp_path / "extension.py"
    target.write_text(
        """from graphql import GraphQLResolveInfo
from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def resolve(self, next_, root, info: GraphQLResolveInfo, **kwargs):
        return next_(root, info, **kwargs)
"""
    )

    result = cli_runner.invoke(
        cli_app,
        ["upgrade", "schema-extension-info", str(target)],
    )

    assert result.exit_code == 1
    assert "1 files changed\n  - 0 files skipped" in result.stdout
    assert "strawberry_info: strawberry.Info" in target.read_text()
    assert "info = strawberry_info._raw_info" in target.read_text()


def test_upgrade_reports_schema_extension_info_warning(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
) -> None:
    target = tmp_path / "extension.py"
    target.write_text(
        """from strawberry.extensions import SchemaExtension


class MyExtension(SchemaExtension):
    def resolve(self, next_, root, info: CustomInfo, **kwargs):
        return next_(root, info, **kwargs)
"""
    )

    result = cli_runner.invoke(
        cli_app,
        ["upgrade", "schema-extension-info", str(target)],
    )

    assert result.exit_code == 0
    assert "Warnings:" in result.stdout
    assert "not a recognized" in result.stdout
    assert "0 files changed\n  - 1 files skipped" in result.stdout


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

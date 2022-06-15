from pathlib import Path
from typing import List

import pytest

from strawberry.cli.commands.codegen import ConsolePlugin, codegen as cmd_codegen
from strawberry.codegen import CodegenFile, CodegenResult, QueryCodegenPlugin
from strawberry.codegen.types import GraphQLOperation, GraphQLType


class ConsoleTestPlugin(ConsolePlugin):
    def on_end(self, result: CodegenResult):
        result.files[0].path = "renamed.py"

        return super().on_end(result)


class QueryCodegenTestPlugin(QueryCodegenPlugin):
    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> List[CodegenFile]:
        return [
            CodegenFile(
                path="test.py",
                content=f"# This is a test file for {operation.name}",
            )
        ]


class EmptyPlugin(QueryCodegenPlugin):
    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> List[CodegenFile]:
        return [
            CodegenFile(
                path="test.py",
                content="# Empty",
            )
        ]


@pytest.fixture
def query_file_path(tmp_path: Path) -> Path:
    output_path = tmp_path / "query.graphql"
    output_path.write_text(
        """
        query GetUser {
            user {
                name
            }
        }
        """
    )
    return output_path


def test_codegen(cli_runner, query_file_path: Path, tmp_path: Path):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cmd_codegen,
        [
            "-p",
            "tests.cli.test_codegen:QueryCodegenTestPlugin",
            "-o",
            str(tmp_path),
            "--schema",
            selector,
            str(query_file_path),
        ],
    )

    assert result.exit_code == 0

    code_path = tmp_path / "test.py"

    assert code_path.exists()
    assert code_path.read_text() == "# This is a test file for GetUser"


def test_codegen_passing_plugin_symbol(
    cli_runner, query_file_path: Path, tmp_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cmd_codegen,
        [
            "-p",
            "tests.cli.test_codegen:EmptyPlugin",
            "-o",
            str(tmp_path),
            "--schema",
            selector,
            str(query_file_path),
        ],
    )

    assert result.exit_code == 0

    code_path = tmp_path / "test.py"

    assert code_path.exists()
    assert code_path.read_text() == "# Empty"


def test_codegen_returns_error_when_symbol_does_not_exist(
    cli_runner, query_file_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cmd_codegen,
        [
            "-p",
            "tests.cli.test_codegen:SomePlugin",
            "--schema",
            selector,
            str(query_file_path),
        ],
    )

    assert result.exit_code == 1
    assert result.exception.args == (
        "module 'tests.cli.test_codegen' has no attribute 'SomePlugin'",
    )


def test_codegen_returns_error_when_module_does_not_exist(
    cli_runner, query_file_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cmd_codegen,
        ["-p", "fake_module_plugin", "--schema", selector, str(query_file_path)],
    )

    assert result.exit_code == 1
    assert "Error: Plugin fake_module_plugin not found" in result.output


def test_codegen_returns_error_when_does_not_find_plugin(
    cli_runner, query_file_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cmd_codegen,
        ["-p", "tests.cli.test_server", "--schema", selector, str(query_file_path)],
    )

    assert result.exit_code == 1
    assert "Error: Plugin tests.cli.test_server not found" in result.output


def test_codegen_finds_our_plugins(cli_runner, query_file_path: Path, tmp_path: Path):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cmd_codegen,
        ["-p", "python", "--schema", selector, "-o", tmp_path, str(query_file_path)],
    )

    assert result.exit_code == 0

    code_path = tmp_path / "types.py"

    assert code_path.exists()
    assert "class GetUserResult" in code_path.read_text()


def test_can_use_custom_cli_plugin(cli_runner, query_file_path: Path, tmp_path: Path):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cmd_codegen,
        [
            "--cli-plugin",
            "tests.cli.test_codegen:ConsoleTestPlugin",
            "-p",
            "python",
            "--schema",
            selector,
            "-o",
            tmp_path,
            str(query_file_path),
        ],
    )

    assert result.exit_code == 0

    code_path = tmp_path / "renamed.py"

    assert code_path.exists()
    assert "class GetUserResult" in code_path.read_text()

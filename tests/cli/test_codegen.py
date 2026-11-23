from pathlib import Path

import pytest
from typer import Typer
from typer.testing import CliRunner

from strawberry.cli.commands.codegen import ConsolePlugin
from strawberry.codegen import CodegenFile, CodegenResult, QueryCodegenPlugin
from strawberry.codegen.types import GraphQLOperation, GraphQLType


class ConsoleTestPlugin(ConsolePlugin):
    def on_end(self, result: CodegenResult):
        result.files[0].path = "renamed.py"

        return super().on_end(result)


class QueryCodegenTestPlugin(QueryCodegenPlugin):
    def generate_code(
        self, types: list[GraphQLType], operation: GraphQLOperation
    ) -> list[CodegenFile]:
        return [
            CodegenFile(
                path="test.py",
                content=f"# This is a test file for {operation.name}",
            )
        ]


class EmptyPlugin(QueryCodegenPlugin):
    def generate_code(
        self, types: list[GraphQLType], operation: GraphQLOperation
    ) -> list[CodegenFile]:
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


@pytest.fixture
def query_file_path2(tmp_path: Path) -> Path:
    output_path = tmp_path / "query2.graphql"
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


def test_codegen(
    cli_app: Typer, cli_runner: CliRunner, query_file_path: Path, tmp_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
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


def test_codegen_multiple_files(
    cli_app: Typer,
    cli_runner: CliRunner,
    query_file_path: Path,
    query_file_path2: Path,
    tmp_path: Path,
):
    expected_paths = [
        tmp_path / "query.py",
        tmp_path / "query2.py",
        tmp_path / "query.ts",
        tmp_path / "query2.ts",
    ]
    for path in expected_paths:
        assert not path.exists()

    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "python",
            "-p",
            "typescript",
            "-o",
            str(tmp_path),
            "--schema",
            selector,
            str(query_file_path),
            str(query_file_path2),
        ],
    )

    assert result.exit_code == 0

    for path in expected_paths:
        assert path.exists()
        assert " GetUserResult" in path.read_text()


def test_codegen_pass_no_query(cli_app: Typer, cli_runner: CliRunner, tmp_path: Path):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "tests.cli.test_codegen:EmptyPlugin",
            "-o",
            str(tmp_path),
            "--schema",
            selector,
        ],
    )

    assert result.exit_code == 0


def test_codegen_passing_plugin_symbol(
    cli_app: Typer, cli_runner: CliRunner, query_file_path: Path, tmp_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
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
    cli_app: Typer, cli_runner: CliRunner, query_file_path: Path, tmp_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "tests.cli.test_codegen:SomePlugin",
            "--schema",
            selector,
            "-o",
            str(tmp_path),
            str(query_file_path),
        ],
    )

    assert result.exit_code == 1
    assert result.exception
    assert result.exception.args == (
        "module 'tests.cli.test_codegen' has no attribute 'SomePlugin'",
    )


def test_codegen_returns_error_when_module_does_not_exist(
    cli_app: Typer, cli_runner: CliRunner, query_file_path: Path, tmp_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "fake_module_plugin",
            "--schema",
            selector,
            "-o",
            str(tmp_path),
            str(query_file_path),
        ],
    )

    assert result.exit_code == 1
    assert "Error: Plugin fake_module_plugin not found" in result.output


def test_codegen_returns_error_when_does_not_find_plugin(
    cli_app: Typer, cli_runner: CliRunner, query_file_path: Path, tmp_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "tests.cli.test_server",
            "--schema",
            selector,
            "-o",
            str(tmp_path),
            str(query_file_path),
        ],
    )

    assert result.exit_code == 1
    assert "Error: Plugin tests.cli.test_server not found" in result.output


def test_codegen_finds_our_plugins(
    cli_app: Typer, cli_runner: CliRunner, query_file_path: Path, tmp_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "python",
            "--schema",
            selector,
            "-o",
            str(tmp_path),
            str(query_file_path),
        ],
    )

    assert result.exit_code == 0

    code_path = tmp_path / query_file_path.with_suffix(".py").name

    assert code_path.exists()
    assert "class GetUserResult" in code_path.read_text()


def test_can_use_custom_cli_plugin(
    cli_app: Typer, cli_runner: CliRunner, query_file_path: Path, tmp_path: Path
):
    selector = "tests.fixtures.sample_package.sample_module:schema"
    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "--cli-plugin",
            "tests.cli.test_codegen:ConsoleTestPlugin",
            "-p",
            "python",
            "--schema",
            selector,
            "-o",
            str(tmp_path),
            str(query_file_path),
        ],
    )

    assert result.exit_code == 0

    code_path = tmp_path / "renamed.py"

    assert code_path.exists()
    assert "class GetUserResult" in code_path.read_text()


def _write_fragment_queries(tmp_path: Path) -> list[Path]:
    fragments = """
        fragment AFields on A { name }
        fragment UserFields on User {
            name
            role
            exampleScalar
            unionExample { ... on A { ...AFields } ... on B { a { ...AFields } } }
        }
    """
    viewer = tmp_path / "viewer.graphql"
    viewer.write_text(
        fragments
        + "query Viewer { user { ...UserFields } other: user { exampleScalar role } }",
    )
    issue = tmp_path / "issue.graphql"
    issue.write_text(
        fragments + "query Issue { user { ...UserFields } }",
    )
    plain = tmp_path / "plain.graphql"
    plain.write_text("query Plain { user { name } }")
    return [viewer, issue, plain]


def _run_shared_fragments(
    cli_app: Typer, cli_runner: CliRunner, queries: list[Path], out: Path
):
    out.mkdir()
    return cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "python",
            "--shared-fragments",
            "-o",
            str(out),
            "--schema",
            "tests.fixtures.sample_package.sample_module:schema",
            *map(str, queries),
        ],
    )


def test_codegen_shared_fragments(
    cli_app: Typer,
    cli_runner: CliRunner,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    queries = _write_fragment_queries(tmp_path)
    out = tmp_path / "out"

    result = _run_shared_fragments(cli_app, cli_runner, queries, out)

    assert result.exit_code == 0
    assert (out / "fragments.py").exists()
    viewer_src = (out / "viewer.py").read_text()
    plain_src = (out / "plain.py").read_text()
    assert "class UserFields" not in viewer_src
    assert "NewType" not in viewer_src
    assert "Enum" not in viewer_src
    assert "class UserFields" not in (out / "issue.py").read_text()
    assert "fragments" not in plain_src
    assert (out / "fragments.py").read_text().count("class UserFields:") == 1

    monkeypatch.syspath_prepend(str(out))
    import importlib
    import sys

    for mod in ("fragments", "viewer", "issue", "plain"):
        monkeypatch.delitem(sys.modules, mod, raising=False)

    viewer = importlib.import_module("viewer")
    issue = importlib.import_module("issue")
    plain = importlib.import_module("plain")
    assert viewer.UserFields is issue.UserFields
    assert plain.PlainResult is not None
    assert importlib.import_module("fragments").AFields is not None


def test_codegen_without_shared_fragments_duplicates_classes(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
):
    queries = _write_fragment_queries(tmp_path)
    out = tmp_path / "out"
    out.mkdir()

    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "python",
            "-o",
            str(out),
            "--schema",
            "tests.fixtures.sample_package.sample_module:schema",
            *map(str, queries),
        ],
    )

    assert result.exit_code == 0
    assert not (out / "fragments.py").exists()
    assert "class UserFields" in (out / "viewer.py").read_text()
    assert "class UserFields" in (out / "issue.py").read_text()


def test_codegen_shared_fragments_optional_and_list_fields(
    cli_app: Typer,
    cli_runner: CliRunner,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    app_file = tmp_path / "app_schema.py"
    app_file.write_text(
        """
from typing import Optional
import strawberry

@strawberry.type
class User:
    id: strawberry.ID
    nickname: Optional[str] = None

@strawberry.type
class Query:
    @strawberry.field
    def viewer(self) -> Optional[User]:
        return None

    @strawberry.field
    def users(self) -> list[Optional[User]]:
        return []

schema = strawberry.Schema(query=Query)
"""
    )
    q1 = tmp_path / "viewer.graphql"
    q1.write_text(
        "fragment UserSummary on User { id nickname } "
        "query Viewer { viewer { ...UserSummary } users { ...UserSummary } }"
    )
    q2 = tmp_path / "directory.graphql"
    q2.write_text(
        "fragment UserSummary on User { id nickname } "
        "query Directory { users { ...UserSummary } }"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    out = tmp_path / "out"
    out.mkdir()

    result = cli_runner.invoke(
        cli_app,
        [
            "codegen",
            "-p",
            "python",
            "--shared-fragments",
            "-o",
            str(out),
            "--schema",
            "app_schema:schema",
            str(q1),
            str(q2),
        ],
    )

    assert result.exit_code == 0, result.output
    monkeypatch.syspath_prepend(str(out))
    import importlib
    import sys

    for mod in ("app_schema", "fragments", "viewer", "directory"):
        monkeypatch.delitem(sys.modules, mod, raising=False)

    viewer = importlib.import_module("viewer")
    directory = importlib.import_module("directory")
    assert viewer.UserSummary is directory.UserSummary


def test_codegen_shared_fragments_module_name_collision(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
):
    plain_fragments = tmp_path / "fragments.graphql"
    plain_fragments.write_text("query Fragments { user { name } }")
    ok_result = _run_shared_fragments(
        cli_app, cli_runner, [plain_fragments], tmp_path / "out_ok"
    )
    assert ok_result.exit_code == 0
    assert (tmp_path / "out_ok" / "fragments.py").exists()

    colliding = tmp_path / "fragments.graphql"
    colliding.write_text(
        "fragment F on User { name } query Fragments { user { ...F } }"
    )
    bad_result = _run_shared_fragments(
        cli_app, cli_runner, [colliding], tmp_path / "out_bad"
    )
    assert bad_result.exit_code != 0
    assert "collides with the shared fragments module" in str(bad_result.exception)


def test_codegen_shared_fragments_conflicting_definitions(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
):
    a = tmp_path / "a.graphql"
    a.write_text("fragment F on User { name } query A { user { ...F } }")
    b = tmp_path / "b.graphql"
    b.write_text("fragment F on User { age } query B { user { ...F } }")
    out = tmp_path / "out"

    result = _run_shared_fragments(cli_app, cli_runner, [a, b], out)

    assert result.exit_code != 0
    assert "F is defined differently" in str(result.exception)
    assert list(out.iterdir()) == []


def test_codegen_shared_fragments_conflicting_directives(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
):
    a = tmp_path / "a.graphql"
    a.write_text("fragment F on User { name } query A { user { ...F } }")
    b = tmp_path / "b.graphql"
    b.write_text(
        "fragment F on User { name @skip(if: true) } query B { user { ...F } }"
    )
    out = tmp_path / "out"

    result = _run_shared_fragments(cli_app, cli_runner, [a, b], out)

    assert result.exit_code != 0
    assert "F is defined differently" in str(result.exception)
    assert list(out.iterdir()) == []


def test_codegen_shared_fragments_root_fragment_spread(
    cli_app: Typer,
    cli_runner: CliRunner,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    root_q = tmp_path / "root_query.graphql"
    root_q.write_text(
        "fragment QueryFields on Query { user { name } } query Root { ...QueryFields }"
    )
    out = tmp_path / "out"

    result = _run_shared_fragments(cli_app, cli_runner, [root_q], out)

    assert result.exit_code == 0, result.output
    root_src = (out / "root_query.py").read_text()
    assert "from fragments import QueryFields" in root_src
    assert "class QueryFields:" in (out / "fragments.py").read_text()

    monkeypatch.syspath_prepend(str(out))
    import importlib
    import sys

    for mod in ("fragments", "root_query"):
        monkeypatch.delitem(sys.modules, mod, raising=False)

    root_mod = importlib.import_module("root_query")
    fragments_mod = importlib.import_module("fragments")
    assert root_mod.QueryFields is fragments_mod.QueryFields


def test_codegen_shared_fragments_reverse_module_name_collision(
    cli_app: Typer, cli_runner: CliRunner, tmp_path: Path
):
    plain_fragments = tmp_path / "fragments.graphql"
    plain_fragments.write_text("query Fragments { user { name } }")
    uses_fragment = tmp_path / "viewer.graphql"
    uses_fragment.write_text(
        "fragment F on User { name } query Viewer { user { ...F } }"
    )
    out = tmp_path / "out"

    result = _run_shared_fragments(
        cli_app, cli_runner, [plain_fragments, uses_fragment], out
    )

    assert result.exit_code != 0
    assert "collides with the shared fragments module" in str(result.exception)
    assert list(out.iterdir()) == []

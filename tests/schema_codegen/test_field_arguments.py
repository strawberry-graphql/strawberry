import textwrap

from strawberry.schema_codegen import codegen


def test_field_arguments_are_emitted_as_resolver_parameters():
    schema = """
    input IssueCreateInput {
      title: String!
    }

    type Issue {
      id: ID!
      comments(first: Int): [String!]!
    }

    type Query {
      issue(id: ID!): Issue
    }

    type Mutation {
      issueCreate(input: IssueCreateInput!): Issue
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry

        @strawberry.input
        class IssueCreateInput:
            title: str

        @strawberry.type
        class Issue:
            id: strawberry.ID
            @strawberry.field
            def comments(self, first: int | None) -> list[str]:
                raise NotImplementedError

        @strawberry.type
        class Query:
            @strawberry.field
            def issue(self, id: strawberry.ID) -> Issue | None:
                raise NotImplementedError

        @strawberry.type
        class Mutation:
            @strawberry.field
            def issue_create(self, input: IssueCreateInput) -> Issue | None:
                raise NotImplementedError

        schema = strawberry.Schema(query=Query, mutation=Mutation)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_field_argument_defaults_are_preserved():
    schema = """
    type Query {
      greet(name: String = "world", times: Int! = 2): String!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry

        @strawberry.type
        class Query:
            @strawberry.field
            def greet(self, name: str | None = "world", times: int = 2) -> str:
                raise NotImplementedError

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_required_argument_after_defaulted_argument_is_keyword_only():
    schema = """
    type Query {
      search(term: String = "all", limit: Int!): String!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry

        @strawberry.type
        class Query:
            @strawberry.field
            def search(self, *, term: str | None = "all", limit: int) -> str:
                raise NotImplementedError

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_keyword_argument_uses_strawberry_argument_name():
    schema = """
    type Query {
      greet(from: String!): String!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from typing import Annotated

        @strawberry.type
        class Query:
            @strawberry.field
            def greet(self, from_: Annotated[str, strawberry.argument(name="from")]) -> str:
                raise NotImplementedError

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_generated_schema_round_trips_field_arguments():
    schema = """
    input IssueCreateInput {
      title: String!
    }

    type Issue {
      id: ID!
      comments(first: Int): [String!]!
    }

    type Query {
      issue(id: ID!): Issue
    }

    type Mutation {
      issueCreate(input: IssueCreateInput!): Issue
    }
    """

    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp_dir:
        module_path = Path(tmp_dir) / "generated.py"
        module_path.write_text(codegen(schema))

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import generated; print(generated.schema)",
            ],
            cwd=tmp_dir,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    assert result.returncode == 0, (
        f"Generated module should import and build a schema; stderr: {result.stderr}"
    )

    printed = result.stdout

    assert "issue(id: ID!): Issue" in printed
    assert "comments(first: Int): [String!]!" in printed
    assert "issueCreate(input: IssueCreateInput!): Issue" in printed
    assert "input IssueCreateInput" in printed

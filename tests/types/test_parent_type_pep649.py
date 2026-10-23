"""Tests for strawberry.Parent with PEP 649 deferred annotation evaluation.

On Python 3.14+, annotations are lazily evaluated via __annotate__ (PEP 649).
When a resolver references a type via strawberry.Parent[SomeType] and SomeType
is defined after the resolver (forward reference), the deferred evaluation of
annotations can raise NameError when inspect.Signature.from_callable() triggers
__annotate__. This test verifies that strawberry handles this case correctly
by falling back to FORWARDREF format.
"""

import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="PEP 649 deferred annotations require Python 3.14+",
)


def test_parent_forward_ref_pep649():
    """Test that strawberry.Parent works with forward references under PEP 649.

    The resolver is defined before the class it references via strawberry.Parent,
    which causes a NameError during deferred annotation evaluation on Python 3.14+.
    """
    code = textwrap.dedent("""\
        import strawberry

        def get_full_name(user: strawberry.Parent[User]) -> str:
            return f"{user.first_name} {user.last_name}"

        @strawberry.type
        class User:
            first_name: str
            last_name: str
            full_name: str = strawberry.field(resolver=get_full_name)

        @strawberry.type
        class Query:
            @strawberry.field
            def user(self) -> User:
                return User(first_name="John", last_name="Doe")

        schema = strawberry.Schema(query=Query)

        query = "{ user { firstName, lastName, fullName } }"
        result = schema.execute_sync(query)
        assert not result.errors, f"Unexpected errors: {result.errors}"
        assert result.data == {
            "user": {
                "firstName": "John",
                "lastName": "Doe",
                "fullName": "John Doe",
            }
        }
        print("OK")
    """)

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Process failed with:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "OK" in result.stdout


def test_parent_forward_ref_pep649_async():
    """Test that async resolvers with strawberry.Parent forward refs work under PEP 649."""
    code = textwrap.dedent("""\
        import asyncio
        import strawberry

        async def get_children(parent: strawberry.Parent[TreeNode]) -> list[str]:
            return [f"child_of_{parent.name}"]

        @strawberry.type
        class TreeNode:
            name: str
            children: list[str] = strawberry.field(resolver=get_children)

        @strawberry.type
        class Query:
            @strawberry.field
            def node(self) -> TreeNode:
                return TreeNode(name="root")

        schema = strawberry.Schema(query=Query)

        query = "{ node { name, children } }"
        result = asyncio.run(schema.execute(query))
        assert not result.errors, f"Unexpected errors: {result.errors}"
        assert result.data == {
            "node": {
                "name": "root",
                "children": ["child_of_root"],
            }
        }
        print("OK")
    """)

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Process failed with:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "OK" in result.stdout


def test_parent_no_forward_ref_still_works():
    """Ensure that normal (non-forward-ref) strawberry.Parent still works on 3.14+."""
    code = textwrap.dedent("""\
        import strawberry

        @strawberry.type
        class User:
            first_name: str
            last_name: str

        def get_full_name(user: strawberry.Parent[User]) -> str:
            return f"{user.first_name} {user.last_name}"

        @strawberry.type
        class UserWithFullName:
            first_name: str
            last_name: str
            full_name: str = strawberry.field(resolver=get_full_name)

        @strawberry.type
        class Query:
            @strawberry.field
            def user(self) -> UserWithFullName:
                return UserWithFullName(first_name="Jane", last_name="Doe")

        schema = strawberry.Schema(query=Query)
        result = schema.execute_sync("{ user { fullName } }")
        assert not result.errors, f"Unexpected errors: {result.errors}"
        assert result.data == {"user": {"fullName": "Jane Doe"}}
        print("OK")
    """)

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Process failed with:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "OK" in result.stdout

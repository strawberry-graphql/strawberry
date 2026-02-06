import textwrap

from strawberry.schema_codegen import codegen


def test_generates_used_interface_before():
    schema = """
    type Human implements Being {
        id: ID!
        name: String!
        friends: [Human]
    }

    type Cat implements Being {
        id: ID!
        name: String!
        livesLeft: Int
    }

    interface Being {
        id: ID!
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.interface
        class Being:
            id: strawberry.ID
            name: str

        @strawberry.type
        class Human(Being):
            id: strawberry.ID
            name: str
            friends: list[Human | None] | None

        @strawberry.type
        class Cat(Being):
            id: strawberry.ID
            name: str
            lives_left: int | None
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_generates_implementing_type_before_referencing_type():
    """Types that implement an interface must be emitted before types that reference them.

    Otherwise the referencing type (e.g. FooContainer with foo: Foo) would be
    defined before Foo, causing NameError when the module is loaded.
    """
    schema = """
    interface Bar {
        bar: String!
    }

    type Foo implements Bar {
        bar: String!
    }

    type FooContainer {
        foo: Foo!
    }
    """

    generated = codegen(schema).strip()

    # Bar (interface) must appear first
    bar_pos = generated.index("@strawberry.interface\nclass Bar:")
    # Foo (implements Bar) must appear before FooContainer (which references Foo)
    foo_pos = generated.index("@strawberry.type\nclass Foo(Bar):")
    foo_container_pos = generated.index("@strawberry.type\nclass FooContainer:")

    assert bar_pos < foo_pos < foo_container_pos, (
        "Order should be Bar, Foo, FooContainer so Foo is defined before FooContainer"
    )


def test_generated_module_imports_without_name_error():
    """Generated code that references implementing types must be importable."""
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    schema = """
    interface Bar {
        bar: String!
    }
    type Foo implements Bar {
        bar: String!
    }
    type FooContainer {
        foo: Foo!
    }
    """
    code = codegen(schema)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import runpy; runpy.run_path({path!r})"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        assert result.returncode == 0, (
            f"Generated module should import without error; stderr: {result.stderr}"
        )
    finally:
        Path(path).unlink()

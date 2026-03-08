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
        from __future__ import annotations
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


def test_forward_reference_in_field_annotation():
    """A type can reference another type that appears later in the generated output.

    The generated ``from __future__ import annotations`` (PEP 563) defers
    evaluation of annotations, so ``foo: Foo`` does not require ``Foo`` to be
    defined at class-creation time.
    """
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    schema = """
    type FooContainer {
        foo: Foo!
    }

    type Foo {
        name: String!
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


def test_generates_union_members_before_union():
    """Union member types must be emitted before the union definition.

    The generated union assignment (e.g.
    ``FooOrBar = Annotated[Foo | Bar, strawberry.union(...)]``) is a runtime
    expression, not an annotation, so ``from __future__ import annotations``
    would not defer its evaluation.  The member types must therefore be defined
    before the union line.
    """
    schema = """
    interface Base {
        id: ID!
    }

    type Foo implements Base {
        id: ID!
        name: String!
    }

    type Bar implements Base {
        id: ID!
        title: String!
    }

    union FooOrBar = Foo | Bar
    """

    generated = codegen(schema).strip()

    base_pos = generated.index("@strawberry.interface\nclass Base:")
    foo_pos = generated.index("@strawberry.type\nclass Foo(Base):")
    bar_pos = generated.index("@strawberry.type\nclass Bar(Base):")
    union_pos = generated.index("FooOrBar = Annotated[")

    assert base_pos < foo_pos, "Interface must precede implementing type"
    assert base_pos < bar_pos, "Interface must precede implementing type"
    assert foo_pos < union_pos, "Union members must precede union definition"
    assert bar_pos < union_pos, "Union members must precede union definition"

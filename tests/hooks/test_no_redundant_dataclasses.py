from textwrap import dedent

from strawberry.hooks.no_redundant_dataclasses import main


def test_check_namespaced_decorator(tmp_path):
    code = """
    import strawberry
    import dataclasses

    @dataclasses.dataclass
    @strawberry.type
    class Foo: ...
    """
    file = tmp_path / "foo.py"
    file.write_text(dedent(code), encoding="utf-8")
    exit_code = main([str(file)])
    assert exit_code == 1


def test_check_imported_decorator(tmp_path):
    code = """
    import strawberry
    from dataclasses import dataclass

    @dataclass
    @strawberry.type
    class Foo: ...
    """
    file = tmp_path / "foo.py"
    file.write_text(dedent(code), encoding="utf-8")
    exit_code = main([str(file)])
    assert exit_code == 1


def test_check_passing_file(tmp_path):
    code = """
    import strawberry

    @strawberry.type
    class Foo: ...
    """
    file = tmp_path / "foo.py"
    file.write_text(dedent(code), encoding="utf-8")
    exit_code = main([str(file)])
    assert exit_code == 0

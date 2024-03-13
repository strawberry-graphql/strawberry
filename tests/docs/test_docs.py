import dataclasses
import inspect
import json
import re
import typing
from pathlib import Path
from textwrap import dedent
from uuid import UUID, uuid4

import pytest
from pytest_examples import CodeExample, EvalExample
from tests.docs import common

import strawberry
from strawberry.printer import print_schema

DOC_PATH = ""
DOC_GLOBALS = {}


def remove_indent(text: str) -> typing.Tuple[str, int]:
    """Adapted from pytest_examples module."""
    first_line_before = text[: text.strip("\n").find("\n")]
    text = dedent(text)
    first_line_after = text[: text.strip("\n").find("\n")]
    return text, len(first_line_before) - len(first_line_after)


def _extract_code_chunks(
    path: Path,
    text: str,
    group: UUID,
    *,
    line_offset: int = 0,
    index_offset: int = 0,
    code_prefixes: typing.Optional[typing.List[str]] = None,
) -> typing.Iterable[CodeExample]:
    """Adapted from pytest_examples module. Expanded to look for other code types."""
    for m_code in re.finditer(r"(^ *```)( *)(.*?)\n(.+?)\1", text, flags=re.M | re.S):
        group1, group2, prefix, source = m_code.groups()
        prefix = prefix.lower()

        # Filter out based on code prefixes
        if code_prefixes and not prefix.startswith(code_prefixes):
            continue

        start_line = line_offset + text[: m_code.start()].count("\n") + 1
        source_dedent, indent = remove_indent(source)
        # 1 for the newline
        start_index = (
            index_offset + m_code.start() + len(group1) + len(group2) + len(prefix) + 1
        )
        yield CodeExample(
            source=source_dedent,
            path=path,
            start_line=start_line,
            end_line=start_line + source.count("\n") + 1,
            start_index=start_index,
            end_index=start_index + len(source),
            prefix=prefix,
            indent=indent,
            group=group,
        )


def find_examples(
    *paths: typing.Union[str, Path],
    skip: bool = False,
) -> typing.Iterable[CodeExample]:
    """Adapted from pytest_examples module. Expanded to look for other code types."""
    if skip:
        return

    for s in paths:
        path = Path(s)
        if path.is_file():
            sub_paths = [path]
        elif path.is_dir():
            sub_paths = path.glob("**/*")
        else:
            raise ValueError(f"Not a file or directory: {s!r}")

        for path in sub_paths:
            group = uuid4()
            if path.suffix == ".py":
                code = path.read_text("utf-8")
                for m_docstring in re.finditer(
                    r'(^ *)(r?""")(.+?)\1"""', code, flags=re.M | re.S
                ):
                    start_line = code[: m_docstring.start()].count("\n")
                    docstring = m_docstring.group(3)
                    index_offset = (
                        m_docstring.start()
                        + len(m_docstring.group(1))
                        + len(m_docstring.group(2))
                    )
                    yield from _extract_code_chunks(
                        path,
                        docstring,
                        group,
                        line_offset=start_line,
                        index_offset=index_offset,
                    )
            elif path.suffix == ".md":
                code = path.read_text("utf-8")
                yield from _extract_code_chunks(path, code, group)


@pytest.mark.parametrize(
    "example",
    [
        *find_examples("docs/index.md"),
        *find_examples("docs/general/"),
        *find_examples("docs/guides/field-extensions.md"),
    ],
    ids=str,
)
def test_docs(example: CodeExample, eval_example: EvalExample):
    global DOC_PATH
    global DOC_GLOBALS

    # Reset saved modules for each new doc file
    if example.path != DOC_PATH:
        DOC_PATH = example.path
        DOC_GLOBALS = {}
        DOC_GLOBALS.update(common.modules)

    eval_example.set_config(
        ruff_ignore=[
            "F821",  # Ignore imports
            "T201",  # Ignore print statments
        ],
    )

    if example.prefix == "python":
        check_python_code(example, eval_example)
    elif example.prefix == "python+schema":
        example.source, expected_schema = split_code_example(example.source)
        check_python_code(example, eval_example)

        schema = construct_schema()
        actual_schema = print_schema(schema=schema)

        expected_schema = " ".join(expected_schema.split())
        actual_schema = " ".join(actual_schema.split())

        # Expected schema is likely to be a subset of the overall schema
        assert expected_schema in actual_schema
    elif example.prefix == "graphql+response":
        check_gql_and_response(example)


def split_code_example(source_code: str) -> typing.Tuple[str, typing.Optional[str]]:
    if "---" in source_code:
        return source_code.split("---", 1)

    return (source_code, None)


def check_python_code(example: CodeExample, eval_example: EvalExample):
    eval_example.lint(example)
    example.source = example.source.replace("from api.schema import schema", "")

    # Save off module namespace for the same file
    saved_modules = eval_example.run(
        example,
        # Add these imports automatically for testing
        module_globals=DOC_GLOBALS,
    )
    DOC_GLOBALS.update(saved_modules)


def construct_schema():
    # Try our best to construct a schema
    types = [
        possible_type
        for possible_type in DOC_GLOBALS.values()
        # Make sure it's a strawberry type and not say a FieldExtension
        if inspect.isclass(possible_type) and dataclasses.is_dataclass(possible_type)
    ]

    # Query must exist
    return strawberry.Schema(
        query=DOC_GLOBALS.get("Query"),
        mutation=DOC_GLOBALS.get("Mutation"),
        subscription=DOC_GLOBALS.get("Subscription"),
        types=types,
    )


def check_gql_and_response(example: CodeExample):
    gql_query, expected_response_str = split_code_example(example.source)
    expected_response = json.loads(expected_response_str)
    schema = construct_schema()

    result = schema.execute_sync(
        query=gql_query,
    )

    assert result.errors is None
    assert result.data == expected_response

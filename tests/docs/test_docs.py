import inspect
import typing

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples
from tests.docs import common

import strawberry
from strawberry.printer import print_schema

DOC_PATH = ""
DOC_GLOBALS = {}


@pytest.mark.parametrize(
    "example",
    [
        *find_examples("docs/index.md"),
        *find_examples("docs/general/"),
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

    schema = None
    if example.prefix == "python+schema":
        schema = extract_schema(example)

    eval_example.lint(example)

    # Removes placeholder imports
    example.source = example.source.replace("from api.schema import schema", "")

    # Save off module namespace for the same file
    saved_modules = eval_example.run(
        example,
        # Add these imports automatically for testing
        module_globals=DOC_GLOBALS,
    )
    DOC_GLOBALS.update(saved_modules)

    # Extra checks
    if schema:
        check_schema(schema)


def extract_schema(example: CodeExample) -> typing.Optional[str]:
    """Extracts any schema code blocks from `python+schema` code blocks."""
    schema = None
    if "---" in example.source:
        (example.source, schema) = example.source.split("---", 1)

    return schema


def check_schema(expected_schema: str):
    """Checks the schema code examples in `python+schema` code blocks."""
    if "schema" in DOC_GLOBALS:
        expected_schema = DOC_GLOBALS["schema"]
    else:
        # Try our best to construct a schema
        types = [
            possible_type
            for possible_type in DOC_GLOBALS.values()
            if inspect.isclass(possible_type)
        ]

        expected_schema = strawberry.Schema(query=DOC_GLOBALS["Query"], types=types)

    actual_schema = print_schema(schema=expected_schema)

    # Expected schema is likely to be a subset of the overall schema
    assert str(expected_schema) in actual_schema

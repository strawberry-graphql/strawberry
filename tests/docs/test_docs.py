import typing

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples

import strawberry


@pytest.mark.flaky
@pytest.mark.parametrize(
    "example",
    find_examples("docs"),
    ids=str,
)
def test_docs(example: CodeExample, eval_example: EvalExample):
    eval_example.set_config(
        ruff_ignore=[
            # Ignore imports
            "F821",
        ],
    )

    eval_example.lint(example)
    eval_example.run(
        example,
        # Add these imports automatically for testing
        module_globals={
            "strawberry": strawberry,
            "typing": typing,
        },
    )

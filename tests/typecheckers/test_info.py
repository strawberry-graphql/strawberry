from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import Result, typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]


def test_with_params():
    CODE = """
import strawberry

def example(info: strawberry.Info[None, None]) -> None:
    reveal_type(info.context)
    reveal_type(info.root_value)
"""

    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "info.context" is "None"',
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message='Type of "info.root_value" is "None"',
                line=6,
                column=17,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(type="note", message='Revealed type is "None"', line=5, column=17),
            Result(type="note", message='Revealed type is "None"', line=6, column=17),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `None`",
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message="Revealed type: `None`",
                line=6,
                column=17,
            ),
        ]
    )


def test_with_one_param():
    CODE = """
import strawberry

def example(info: strawberry.Info[None]) -> None:
    reveal_type(info.context)
    reveal_type(info.root_value)
"""

    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "info.context" is "None"',
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message='Type of "info.root_value" is "Any"',
                line=6,
                column=17,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(type="note", message='Revealed type is "None"', line=5, column=17),
            Result(type="note", message='Revealed type is "Any"', line=6, column=17),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `None`",
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message="Revealed type: `Any`",
                line=6,
                column=17,
            ),
        ]
    )


def test_without_params():
    CODE = """
import strawberry

def example(info: strawberry.Info) -> None:
    reveal_type(info.context)
    reveal_type(info.root_value)
"""

    results = typecheck(CODE)

    assert results.pyright == snapshot(
        [
            Result(
                type="information",
                message='Type of "info.context" is "Any"',
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message='Type of "info.root_value" is "Any"',
                line=6,
                column=17,
            ),
        ]
    )
    assert results.mypy == snapshot(
        [
            Result(type="note", message='Revealed type is "Any"', line=5, column=17),
            Result(type="note", message='Revealed type is "Any"', line=6, column=17),
        ]
    )
    assert results.ty == snapshot(
        [
            Result(
                type="information",
                message="Revealed type: `Any`",
                line=5,
                column=17,
            ),
            Result(
                type="information",
                message="Revealed type: `Any`",
                line=6,
                column=17,
            ),
        ]
    )


def test_schema_extension_resolve_accepts_strawberry_info():
    code = """
from typing import Any

import strawberry
from strawberry.extensions import SchemaExtension


class Extension(SchemaExtension):
    def resolve(
        self,
        _next: Any,
        root: Any,
        info: strawberry.Info,
        *args: str,
        **kwargs: Any,
    ) -> Any:
        return _next(root, info, *args, **kwargs)
"""

    results = typecheck(code)

    assert results.pyright == snapshot([])
    assert results.mypy == snapshot([])
    assert results.ty == snapshot([])

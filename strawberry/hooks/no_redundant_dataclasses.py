from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class Visitor(ast.NodeVisitor):
    """A linter that finds issues and includes the source code."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        is_strawberry_class = False
        is_raw_dataclass = False

        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Attribute)
                and isinstance(decorator.value, ast.Name)
                and decorator.value.id == "strawberry"
                and decorator.attr == "type"
            ) or (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "strawberry"
                and decorator.func.attr == "type"
            ):
                is_strawberry_class = True

            if (isinstance(decorator, ast.Name) and decorator.id == "dataclass") or (
                isinstance(decorator, ast.Attribute)
                and isinstance(decorator.value, ast.Name)
                and decorator.value.id == "dataclasses"
                and decorator.attr == "dataclass"
            ):
                is_raw_dataclass = True

        if is_strawberry_class and is_raw_dataclass:
            self.errors.append(f":{node.lineno}: {node.name}")

        self.generic_visit(node)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)
    violations: list[str] = []

    for filename in args.filenames:
        with Path(filename).open("rb") as f:
            tree = ast.parse(f.read(), filename=filename)
            visitor = Visitor()
            visitor.visit(tree)
            violations.extend(f"- {filename}{error}" for error in visitor.errors)

    if not violations:
        return 0

    msg = "\n".join(
        (
            "Decorating strawberry types with dataclasses.dataclass is redundant.",
            "Remove the dataclass decorator from the following classes:",
            *violations,
        )
    )

    print(msg)
    return 1

import ast
from inspect import getframeinfo, stack
from pathlib import Path
from typing import Optional, Type

import libcst as cst
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider

from .exception import StrawberryException
from .exception_source import ExceptionSource


class InvalidUnionTypeError(StrawberryException):
    """The union is constructed with an invalid type"""

    invalid_type: Type

    def __init__(self, invalid_type: Type) -> None:
        self.invalid_type = invalid_type

        # assuming that the exception happens two stack frames above the current one.
        # one is our code checking for invalid types, the other is the caller
        self.frame = getframeinfo(stack()[2][0])

        type_name = invalid_type.__name__

        self.message = f"Type `{type_name}` cannot be used in a GraphQL Union"
        self.rich_message = (
            f"Type `[underline]{type_name}[/]` cannot be used in a GraphQL Union"
        )
        self.suggestion = (
            "To fix this error you should replace the type a strawberry.type"
        )
        self.annotation_message = "invalid type here"

    def _get_exception_source(
        self, path: Path, full_source: str, start_line: int, end_line: int
    ) -> ExceptionSource:
        code_lines = full_source.splitlines()[start_line - 1 : end_line]
        code = "\n".join(code_lines)
        error_line = self.find_invalid_type_line(code)
        invalid_type_line = code_lines[error_line]
        error_column = invalid_type_line.find(self.invalid_type.__name__)

        return ExceptionSource(
            path=path,
            code=full_source,
            start_line=start_line,
            end_line=end_line,
            error_line=start_line + error_line,
            error_column=error_column,
            error_column_end=error_column + len(self.invalid_type.__name__),
        )

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        union_position: Optional[CodeRange] = None

        lineno = self.frame.lineno

        class FindStrawberryUnionNode(cst.CSTVisitor):
            METADATA_DEPENDENCIES = (PositionProvider,)

            def visit_Call(self, node: cst.Call) -> Optional[bool]:
                is_union_call = False

                position = self.get_metadata(PositionProvider, node)

                if lineno < position.start.line or lineno > position.end.line:
                    return True

                # this only works when people don't change the imports
                if isinstance(node.func, cst.Name) and node.func.value == "union":
                    is_union_call = True
                elif isinstance(node.func, cst.Attribute):
                    if (
                        isinstance(node.func.value, cst.Name)
                        and node.func.attr.value == "union"
                        and node.func.value.value == "strawberry"
                    ):
                        is_union_call = True

                if is_union_call:
                    nonlocal union_position
                    union_position = position

                return True

        path = Path(self.frame.filename)
        full_source = path.read_text()

        visitor = FindStrawberryUnionNode()

        module = cst.parse_module(full_source)
        wrapper = MetadataWrapper(module)
        wrapper.visit(visitor)

        if not union_position:
            return None

        return self._get_exception_source(
            path=path,
            full_source=full_source,
            start_line=union_position.start.line,
            end_line=union_position.end.line,
        )

    def find_invalid_type_line(self, code: str) -> int:
        lines = code.splitlines()
        invalid_type_line = -1
        type_name = self.invalid_type.__name__

        for invalid_type_line, line in enumerate(lines):
            if type_name in line:
                return invalid_type_line

        raise ValueError(f"Could not find {self.invalid_type.__name__} in {code}")

    # todo: maybe also check difference between a scalar and other types?


class InvalidTypeForUnionMergeError(InvalidUnionTypeError):
    """A specialized version of InvalidUnionTypeError for when trying
    to merge unions with incompatible types"""

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        strawberry_union_node = None

        lineno = self.frame.lineno
        invalid_type_name = self.invalid_type.__name__

        class FindStrawberryUnionNode(ast.NodeVisitor):
            def visit_BinOp(self, node: ast.BinOp) -> None:
                if node.lineno != lineno:
                    return

                if not isinstance(node.op, ast.BitOr):
                    return

                if any(
                    isinstance(arg, ast.Name) and arg.id == invalid_type_name
                    for arg in (node.left, node.right)
                ):
                    nonlocal strawberry_union_node
                    strawberry_union_node = node

        path = Path(self.frame.filename)
        full_source = path.read_text()

        module = ast.parse(full_source)
        FindStrawberryUnionNode().visit(module)

        return (
            self._get_exception_source(
                path=path,
                full_source=full_source,
                start_line=strawberry_union_node.lineno,
                # end_lineno exists from python 3.8+, but this error
                # will only appear in python 3.10, so we can ignore
                # the type error, up until we use libcst for this too
                end_line=strawberry_union_node.end_lineno,  # type: ignore
            )
            if strawberry_union_node
            else None
        )

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple, Type

import libcst as cst
from backports.cached_property import cached_property
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider

from .exception import ExceptionSource, StrawberryException


if TYPE_CHECKING:
    from rich.console import RenderableType

from inspect import getframeinfo, stack


class InvalidUnionTypeError(StrawberryException):
    """The union is constructed with an invalid type"""

    documentation_url = "https://errors.strawberry.rocks/invalid-union-type"
    invalid_type: Type

    def __init__(self, invalid_type: Type) -> None:
        self.invalid_type = invalid_type

        # assuming that the exception happens two stack frames above the current one.
        # one is our code checking for invalid types, the other is the caller
        self.frame = getframeinfo(stack()[2][0])

        message = f"Type `{invalid_type.__name__}` cannot be used in a GraphQL Union"

        super().__init__(message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        strawberry_union_node_position: Optional[CodeRange] = None

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
                    nonlocal strawberry_union_node_position
                    strawberry_union_node_position = position

                return True

        path = Path(self.frame.filename)
        full_source = path.read_text()

        visitor = FindStrawberryUnionNode()

        module = cst.parse_module(full_source)
        wrapper = MetadataWrapper(module)
        wrapper.visit(visitor)

        if not strawberry_union_node_position:
            return None

        start_line = strawberry_union_node_position.start.line
        end_line = strawberry_union_node_position.end.line

        code = "\n".join(full_source.splitlines()[start_line - 1 : end_line])

        return ExceptionSource(
            path=path,
            code=code,
            line=self.frame.lineno,
        )

    def find_invalid_type_line(self) -> Tuple[int, str]:
        assert self.exception_source

        code = self.exception_source.code

        lines = code.splitlines()
        invalid_type_line = -1
        type_name = self.invalid_type.__name__

        for invalid_type_line, line in enumerate(lines):
            if type_name in line:
                return invalid_type_line, line

        raise ValueError(f"Could not find {self.invalid_type.__name__} in {code}")

    @property
    def __rich_header__(self) -> "RenderableType":
        assert self.exception_source

        source_file = self.exception_source.path
        relative_path = self.exception_source.path_relative_to_cwd
        invalid_type_line_no, invalid_type_line = self.find_invalid_type_line()
        error_line: int = self.exception_source.line + invalid_type_line_no

        return (
            f"[bold red]Type `[underline]{self.invalid_type.__name__}[/]` "
            "cannot be used in a GraphQL Union in "
            f"[white][link=file://{source_file}]{relative_path}:{error_line}"
        )

    @property
    def __rich_body__(self) -> "RenderableType":
        assert self.exception_source

        invalid_type_line_no, invalid_type_line = self.find_invalid_type_line()
        column = invalid_type_line.find(self.invalid_type.__name__)

        prefix = " " * column
        caret = "^" * len(self.invalid_type.__name__)

        message = f"{prefix}[bold]{caret}[/] invalid type here"

        error_line: int = self.exception_source.line + invalid_type_line_no
        line_annotations = {error_line: message}

        return self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

    # todo: maybe also check difference between a scalar and other types?

    @property
    def __rich_footer__(self) -> "RenderableType":
        return (
            "To fix this error you should replace the type a strawberry.type "
            "\n\n"
            "Read more about this error on [bold underline]"
            f"[link={self.documentation_url}]{self.documentation_url}"
        )


class InvalidTypeForUnionMergeError(InvalidUnionTypeError):
    """A specialized version of InvalidUnionTypeError for when trying
    to merge unions with incompatible types"""

    @cached_property
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

        if not strawberry_union_node:
            return None

        code = "\n".join(
            full_source.splitlines()[
                strawberry_union_node.lineno - 1 : strawberry_union_node.end_lineno
            ]
        )

        return ExceptionSource(
            path=path,
            code=code,
            line=self.frame.lineno,
        )

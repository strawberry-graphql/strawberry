import ast
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple, Type

from backports.cached_property import cached_property

from .exception import ExceptionSource, StrawberryException


if TYPE_CHECKING:
    from rich.console import RenderableType

from inspect import getframeinfo, stack


class InvalidUnionTypeError(StrawberryException):
    """The union is constructed with an invalid type"""

    documentation_url = "https://errors.strawberry.rocks/invalid-union-type"

    def __init__(self, message: str, invalid_type: Type) -> None:
        super().__init__(message)

        self.invalid_type = invalid_type

        # assuming that the exception happens two stack frames above the current one.
        # one is our code checking for invalid types, the other is the caller
        self.frame = getframeinfo(stack()[2][0])

        # there's two cases here, or maybe 3
        # ---- strawberry.union("Result", (int,)) noqa
        # ---- AUnion | int
        # ---- Union[str, int] done later

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        strawberry_union_node = None

        lineno = self.frame.lineno

        class FindStrawberryUnionNode(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                if node.lineno != lineno:
                    return

                is_union_call = False

                # this only works when people don't change the imports
                if isinstance(node.func, ast.Name) and node.func.id == "union":
                    is_union_call = True
                elif isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.attr == "union"
                        and node.func.value.id == "strawberry"
                    ):
                        is_union_call = True

                    print(node.func.attr, node.lineno)

                if is_union_call:
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

    @property
    def __rich_footer__(self) -> "RenderableType":
        return (
            "To fix this error you should replace the type a strawberry.type "
            "\n\n"
            "Read more about this error on [bold underline]"
            f"[link={self.documentation_url}]{self.documentation_url}"
        )

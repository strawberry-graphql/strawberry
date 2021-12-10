import ast
import inspect
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, NamedTuple, Optional, Union

from backports.cached_property import cached_property
from rich.console import RenderableType

from .syntax import Syntax


class NodeSource(NamedTuple):
    line: int
    column: int


@dataclass
class ExceptionSource:
    path: Path
    code: str
    line: int

    @property
    def path_relative_to_cwd(self) -> Path:
        return self.path.relative_to(Path.cwd())

    @cached_property
    def dedented_code(self) -> str:
        return textwrap.dedent(self.code)

    @cached_property
    def code_padding(self) -> int:
        return max(
            len(x) - len(y)
            for x, y in zip(
                self.code.splitlines(),
                self.dedented_code.splitlines(),
            )
        )

    @cached_property
    def code_ast(self) -> ast.Module:
        return ast.parse(self.dedented_code)

    def find_class_attribute(self, field_name: str) -> Optional[NodeSource]:
        # we know that self.ast is always a `ast.Module` since we parse a file
        # we assume that the first item in the body is a class definition
        # since we are only parsing the code for the class when we are
        # looking for the class attribute
        assert isinstance(self.code_ast.body[0], ast.ClassDef)

        class_node = self.code_ast.body[0]

        assign_expr = next(
            (
                expr
                for expr in class_node.body
                if self.is_attribute(expr, of_name=field_name)
            ),
            None,
        )

        if assign_expr:
            return NodeSource(assign_expr.lineno, assign_expr.col_offset)

        return None

    @staticmethod
    def is_attribute(expr: Union[ast.Expr, ast.stmt], of_name: str) -> bool:
        if not isinstance(expr, ast.Assign):
            return False

        return any(
            isinstance(target, ast.Name) and target.id == of_name
            for target in expr.targets
        )


class StrawberryException(Exception):
    cls: Optional[type] = None

    def __init__(self, message: str, cls: Optional[type] = None) -> None:
        self.cls = cls
        self.message = message

        super().__init__(message)

    def __rich__(self) -> Optional[RenderableType]:
        return self.message

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None

        source_file = inspect.getsourcefile(self.cls)

        if source_file is None:
            return None

        source_lines, line = inspect.getsourcelines(self.cls)

        return ExceptionSource(
            path=Path(source_file), code="".join(source_lines), line=line
        )

    def highlight_code(
        self, error_line: int, line_annotations: Dict[int, str]
    ) -> Syntax:
        assert self.exception_source is not None

        return Syntax(
            code=self.exception_source.code,
            # TODO: relative to exception source line
            highlight_lines={error_line},
            line_offset=self.exception_source.line - 1,
            line_annotations=line_annotations,
        )

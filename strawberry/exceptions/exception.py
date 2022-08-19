import ast
import inspect
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Dict, NamedTuple, Optional, Type, Union

from backports.cached_property import cached_property

from .utils.getsource import getsourcelines


if TYPE_CHECKING:
    from rich.console import RenderableType

    from strawberry.types.fields.resolver import StrawberryResolver

    from .syntax import Syntax


class NodeSource(NamedTuple):
    line: int
    column: int


@dataclass
class ExceptionSource:
    path: Path
    code: str
    start_line: int
    end_line: int
    error_line: int
    error_column: int

    @property
    def path_relative_to_cwd(self) -> Path:
        if self.path.is_absolute():
            return self.path.relative_to(Path.cwd())

        return self.path

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
        if isinstance(expr, ast.Assign):
            return any(
                isinstance(target, ast.Name) and target.id == of_name
                for target in expr.targets
            )

        if isinstance(expr, ast.AnnAssign):
            return isinstance(expr.target, ast.Name) and expr.target.id == of_name

        return False


class ExceptionSourceIsClass:
    cls: Type

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None

        source_file = inspect.getsourcefile(self.cls)

        if source_file is None:
            return None

        source_lines, line = getsourcelines(self.cls)

        return ExceptionSource(
            path=Path(source_file),
            code="".join(source_lines),
            start_line=line,
            error_line=line,
            end_line=line,
            error_column=0,
        )


class ExceptionSourceIsResolver:
    resolver: "StrawberryResolver"

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.resolver is None:
            return None

        resolver = self.resolver.wrapped_func

        source_file = inspect.getsourcefile(resolver)  # type: ignore

        if source_file is None:
            return None

        source_lines, line = getsourcelines(resolver)

        return ExceptionSource(
            path=Path(source_file),
            code="".join(source_lines),
            start_line=line,
            error_line=line,
            end_line=line,
            error_column=0,
        )


class StrawberryException(Exception):
    message: str
    rich_message: str
    suggestion: str
    documentation_url: ClassVar[str]

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        return None

    @property
    def __rich_header__(self) -> "RenderableType":
        assert self.exception_source

        source_file = self.exception_source.path
        relative_path = self.exception_source.path_relative_to_cwd
        error_line = self.exception_source.error_line

        return (
            f"[bold red]error: {self.rich_message}\n"
            f"[white]     @ [link=file://{source_file}]{relative_path}:{error_line}"
        )

    @property
    def __rich_body__(self) -> "RenderableType":
        return ""

    @property
    def __rich_footer__(self) -> "RenderableType":
        return (
            f"{self.suggestion}\n\n"
            "Read more about this error on [bold underline]"
            f"[link={self.documentation_url}]{self.documentation_url}"
        )

    def __rich__(self) -> Optional["RenderableType"]:
        from rich.box import SIMPLE
        from rich.console import Group
        from rich.panel import Panel

        content = (
            self.__rich_header__,
            "",
            self.__rich_body__,
            "",
            self.__rich_footer__,
        )

        if all(x == "" for x in content):
            return self.message

        return Panel.fit(
            Group(*content),
            box=SIMPLE,
        )

    def highlight_code(
        self, error_line: int, line_annotations: Dict[int, str]
    ) -> "Syntax":
        from .syntax import Syntax

        assert self.exception_source is not None

        return Syntax(
            code=self.exception_source.code,
            highlight_lines={error_line},
            line_offset=self.exception_source.start_line - 1,
            line_annotations=line_annotations,
        )

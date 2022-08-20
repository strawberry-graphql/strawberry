import ast
import inspect
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Dict, NamedTuple, Optional, Tuple, Type

import libcst as cst
import libcst.matchers as m
from backports.cached_property import cached_property
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider

from .utils.getsource import getsourcelines


if TYPE_CHECKING:
    from rich.console import RenderableType

    from strawberry.types.fields.resolver import StrawberryResolver

    from .syntax import Syntax


class NodeSource(NamedTuple):
    position: CodeRange
    node: cst.CSTNode


@dataclass
class ExceptionSource:
    path: Path
    code: str
    start_line: int
    end_line: int
    error_line: int
    error_column: int
    error_column_end: int

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
        path = Path(source_file)

        return ExceptionSource(
            path=path,
            code=path.read_text(),
            start_line=line,
            error_line=line,
            end_line=line,
            error_column=0,
            error_column_end=0,
        )


class ExceptionSourceIsClassAttribute:
    cls: Type
    field_name: str

    def _find_attribute_in_class(self, source: str) -> Optional[NodeSource]:
        module = cst.parse_module(source)
        wrapper = MetadataWrapper(module)

        self.position_metadata = wrapper.resolve(PositionProvider)

        class_defs = m.findall(
            wrapper, m.ClassDef(name=m.Name(value=self.cls.__name__))
        )

        _, line = getsourcelines(self.cls)

        class_def = None

        for definition in class_defs:
            position = self.position_metadata[definition]

            if position.start.line >= line:
                class_def = definition

                break

        assert class_def

        attribute_definition = m.findall(
            class_def,
            m.AssignTarget(target=m.Name(value=self.field_name))
            | m.AnnAssign(target=m.Name(value=self.field_name)),
        )[0]

        if isinstance(attribute_definition, cst.AnnAssign):
            attribute_definition = attribute_definition.target

        return NodeSource(
            self.position_metadata[attribute_definition], attribute_definition
        )

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None

        source_file = inspect.getsourcefile(self.cls)

        if source_file is None:
            return None

        path = Path(source_file)
        code = path.read_text()

        node_source = self._find_attribute_in_class(code)

        if node_source is None:
            return None

        return ExceptionSource(
            path=path,
            code=code,
            # TODO: start should be start of the class
            start_line=node_source.position.start.line,
            error_line=node_source.position.start.line,
            end_line=node_source.position.end.line,
            error_column=node_source.position.start.column,
            error_column_end=node_source.position.end.column,
        )


class ExceptionSourceIsResolver:
    resolver: "StrawberryResolver"

    def _find_resolver_node(
        self, source: str, line: int
    ) -> Optional[Tuple[cst.CSTNode, CodeRange]]:
        module = cst.parse_module(source)
        wrapper = MetadataWrapper(module)

        self.position_metadata = wrapper.resolve(PositionProvider)

        function_defs = m.findall(
            wrapper, m.FunctionDef(name=m.Name(value=self.resolver.name))
        )

        for function_def in function_defs:
            position = self.position_metadata[function_def]

            if position.start.line >= line:
                return function_def, position

        return None

    def _find_resolver_definition(self, source: str, line: int) -> Optional[CodeRange]:
        result = self._find_resolver_node(source, line)

        return result[1] if result else None

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.resolver is None:
            return None

        resolver = self.resolver.wrapped_func

        source_file = inspect.getsourcefile(resolver)  # type: ignore

        if source_file is None:
            return None

        path = Path(source_file)
        full_source = path.read_text()
        _, line = getsourcelines(resolver)

        position = self._find_resolver_definition(full_source, line)

        assert position

        function_prefix = len("def ")
        error_column = position.start.column + function_prefix
        error_column_end = error_column + len(self.resolver.name)

        return ExceptionSource(
            path=path,
            code=full_source,
            start_line=position.start.line,
            error_line=position.start.line,
            end_line=position.end.line,
            error_column=error_column,
            error_column_end=error_column_end,
        )


class ExceptionSourceIsResolverArgument(ExceptionSourceIsResolver):
    resolver: "StrawberryResolver"
    argument_name: str

    def _find_argument_definition(self, source: str, line: int) -> CodeRange:
        result = self._find_resolver_node(source, line)

        assert result

        function_def = result[0]

        argument_def = m.findall(
            function_def,
            m.Param(name=m.Name(value=self.argument_name)),
        )

        # TODO: this is a hack to get the argument definition
        return self.position_metadata[argument_def[0]]

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        exception_source = super().exception_source

        if exception_source is None:
            return None

        full_source = exception_source.path.read_text()

        _, line = getsourcelines(self.resolver.wrapped_func)

        resolver_position = self._find_resolver_definition(full_source, line)

        assert resolver_position

        argument_position = self._find_argument_definition(full_source, line)

        # todo include decorators?

        return ExceptionSource(
            path=exception_source.path,
            code=full_source,
            start_line=resolver_position.start.line,
            end_line=resolver_position.end.line,
            error_line=argument_position.start.line,
            error_column=argument_position.start.column,
            error_column_end=argument_position.end.column,
        )


class StrawberryException(Exception):
    message: str
    rich_message: str
    suggestion: str
    annotation_message: str
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
        assert self.exception_source
        exception_source = self.exception_source

        prefix = " " * exception_source.error_column
        caret = "^" * (
            exception_source.error_column_end - exception_source.error_column
        )

        message = self.annotation_message

        message = f"{prefix}[bold]{caret}[/] {message}"

        error_line = exception_source.error_line
        line_annotations = {error_line: message}

        return self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

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
            line_range=(
                self.exception_source.start_line,
                self.exception_source.end_line,
            ),
        )

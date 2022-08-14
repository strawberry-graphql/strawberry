import ast
import inspect
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from backports.cached_property import cached_property

from .exception import ExceptionSource, NodeSource, StrawberryException
from .utils.getsource import getsourcelines


if TYPE_CHECKING:
    from rich.console import RenderableType

    from strawberry.types.fields.resolver import StrawberryResolver


class MissingArgumentsAnnotationsError(StrawberryException):
    """The field is missing the annotation for one or more arguments"""

    documentation_url = "https://errors.strawberry.rocks/missing-arguments-annotations"

    def __init__(self, resolver: "StrawberryResolver", arguments: List[str]):
        self.missing_arguments = arguments
        self.resolver = resolver

        message = (
            f"Missing annotation for {self.missing_arguments_str} "
            f'in field "{self.resolver.name}", did you forget to add it?'
        )

        super().__init__(message)

    @property
    def missing_arguments_str(self):
        arguments = self.missing_arguments

        if len(arguments) == 1:
            return f'argument "{arguments[0]}"'

        head = ", ".join(arguments[:-1])
        return f'arguments "{head}" and "{arguments[-1]}"'

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.resolver is None:
            return None

        resolver = self.resolver.wrapped_func

        source_file = inspect.getsourcefile(resolver)

        if source_file is None:
            return None

        source_lines, line = getsourcelines(resolver)

        return ExceptionSource(
            path=Path(source_file), code="".join(source_lines), line=line
        )

    def find_argument(self, argument_name: str) -> Optional[NodeSource]:
        assert self.exception_source is not None

        code_ast = self.exception_source.code_ast

        assert isinstance(code_ast.body[0], ast.FunctionDef)

        function_node = code_ast.body[0]

        argument = next(
            (arg for arg in function_node.args.args if arg.arg == argument_name),
            None,
        )

        if argument is None:
            return None

        return NodeSource(argument.lineno, argument.col_offset)

    def __rich__(self) -> Optional["RenderableType"]:
        from rich.box import SIMPLE
        from rich.console import Group
        from rich.panel import Panel

        if not self.exception_source:
            return None

        first_argument = self.find_argument(self.missing_arguments[0])

        assert first_argument

        source_file = self.exception_source.path
        relative_path = self.exception_source.path_relative_to_cwd
        error_line = self.exception_source.line + first_argument.line - 1

        prefix = " " * (first_argument.column + self.exception_source.code_padding)
        caret = "^" * len(self.missing_arguments[0])

        first = "first " if len(self.missing_arguments) > 1 else ""
        message = f"{prefix}[bold]{caret}[/] {first}argument missing annotation"

        line_annotations = {error_line: message}

        code = self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

        header = (
            f"[bold red]Missing annotation for {self.missing_arguments_str} in "
            f"`[underline]{self.resolver.name}[/]` "
            f"in [white][link=file://{source_file}]{relative_path}:{error_line}"
        )

        footer = (
            "To fix this error you can add an annotation to the argument "
            f"like so [italic]`{self.missing_arguments[0]}: str`"
            "\n\n"
            "Read more about this error on [bold underline]"
            f"[link={self.documentation_url}]{self.documentation_url}"
        )

        content = (
            header,
            "",
            code,
            "",
            *footer.splitlines(),
        )

        return Panel.fit(
            Group(*content),  # type: ignore
            box=SIMPLE,
        )

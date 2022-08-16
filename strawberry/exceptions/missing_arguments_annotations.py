import ast
from typing import TYPE_CHECKING, List, Optional

from backports.cached_property import cached_property

from .exception import ExceptionSourceIsResolver, NodeSource, StrawberryException


if TYPE_CHECKING:
    from rich.console import RenderableType

    from strawberry.types.fields.resolver import StrawberryResolver


class MissingArgumentsAnnotationsError(ExceptionSourceIsResolver, StrawberryException):
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

    @cached_property
    def first_argument(self) -> Optional[NodeSource]:
        return self.find_argument(self.missing_arguments[0])

    @property
    def __rich_header__(self) -> "RenderableType":
        assert self.first_argument
        assert self.exception_source

        source_file = self.exception_source.path
        relative_path = self.exception_source.path_relative_to_cwd
        error_line: int = self.exception_source.line + self.first_argument.line - 1

        return (
            f"[bold red]Missing annotation for {self.missing_arguments_str} in "
            f"`[underline]{self.resolver.name}[/]` "
            f"in [white][link=file://{source_file}]{relative_path}:{error_line}"
        )

    @property
    def __rich_body__(self) -> "RenderableType":
        assert self.exception_source
        assert self.first_argument

        prefix = " " * (self.first_argument.column + self.exception_source.code_padding)
        caret = "^" * len(self.missing_arguments[0])

        first = "first " if len(self.missing_arguments) > 1 else ""
        message = f"{prefix}[bold]{caret}[/] {first}argument missing annotation"

        error_line: int = self.exception_source.line + self.first_argument.line - 1
        line_annotations = {error_line: message}

        return self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

    @property
    def __rich_footer__(self) -> "RenderableType":
        return (
            "To fix this error you can add an annotation to the argument "
            f"like so [italic]`{self.missing_arguments[0]}: str`"
            "\n\n"
            "Read more about this error on [bold underline]"
            f"[link={self.documentation_url}]{self.documentation_url}"
        )

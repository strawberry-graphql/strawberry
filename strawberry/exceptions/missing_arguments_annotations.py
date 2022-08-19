import ast
from typing import TYPE_CHECKING, List, Optional

from backports.cached_property import cached_property

from .exception import ExceptionSource, ExceptionSourceIsResolver, StrawberryException


if TYPE_CHECKING:
    from rich.console import RenderableType

    from strawberry.types.fields.resolver import StrawberryResolver


class MissingArgumentsAnnotationsError(ExceptionSourceIsResolver, StrawberryException):
    """The field is missing the annotation for one or more arguments"""

    documentation_url = "https://errors.strawberry.rocks/missing-arguments-annotations"

    def __init__(self, resolver: "StrawberryResolver", arguments: List[str]):
        self.missing_arguments = arguments
        self.resolver = resolver

        self.message = (
            f"Missing annotation for {self.missing_arguments_str} "
            f'in field "{self.resolver.name}", did you forget to add it?'
        )
        self.rich_message = (
            f"Missing annotation for {self.missing_arguments_str} in "
            f"`[underline]{self.resolver.name}[/]`"
        )
        self.suggestion = (
            "To fix this error you can add an annotation to the argument "
            f"like so [italic]`{self.missing_arguments[0]}: str`"
        )

    @property
    def missing_arguments_str(self):
        arguments = self.missing_arguments

        if len(arguments) == 1:
            return f'argument "{arguments[0]}"'

        head = ", ".join(arguments[:-1])
        return f'arguments "{head}" and "{arguments[-1]}"'

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        exception_source = super().exception_source

        if exception_source is None:
            return None

        code_ast = exception_source.code_ast

        assert isinstance(code_ast.body[0], ast.FunctionDef)

        function_node = code_ast.body[0]

        argument_name = self.missing_arguments[0]

        argument = next(
            (arg for arg in function_node.args.args if arg.arg == argument_name),
            None,
        )

        if argument is None:
            return None

        return ExceptionSource(
            path=exception_source.path,
            code=exception_source.code,
            start_line=exception_source.start_line,
            end_line=exception_source.end_line,
            error_line=exception_source.start_line + argument.lineno - 1,
            error_column=argument.col_offset,
        )

    @property
    def __rich_body__(self) -> "RenderableType":
        assert self.exception_source

        prefix = " " * (
            self.exception_source.error_column + self.exception_source.code_padding
        )
        caret = "^" * len(self.missing_arguments[0])

        first = "first " if len(self.missing_arguments) > 1 else ""
        message = f"{prefix}[bold]{caret}[/] {first}argument missing annotation"

        error_line: int = self.exception_source.error_line
        line_annotations = {error_line: message}

        return self.highlight_code(
            error_line=error_line, line_annotations=line_annotations
        )

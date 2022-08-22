from pathlib import Path
from typing import Optional, cast

import libcst as cst
import libcst.matchers as m
from libcst.metadata import MetadataWrapper, ParentNodeProvider, PositionProvider

from strawberry.custom_scalar import ScalarDefinition

from .exception import StrawberryException
from .exception_source import ExceptionSource


class ScalarAlreadyRegisteredError(StrawberryException):
    def __init__(
        self,
        scalar_definition: ScalarDefinition,
        other_scalar_definition: ScalarDefinition,
    ):
        self.scalar_definition = scalar_definition

        scalar_name = scalar_definition.name

        assert other_scalar_definition._source_file

        other_path = Path(other_scalar_definition._source_file)
        other_line = other_scalar_definition._source_line

        self.message = f"Scalar `{scalar_name}` has already been registered"
        self.rich_message = (
            f"Scalar `[underline]{scalar_name}[/]` has already been registered"
        )
        self.annotation_message = "scalar defined here"
        self.suggestion = (
            "To fix this error you should either rename the scalar, "
            "or reuse the existing one, defined in "
            f"[bold white][link=file://{other_path}]"
            f"{other_path.relative_to(Path.cwd())}:{other_line}[/]"
        )

        super().__init__(self.message)

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        assert self.scalar_definition._source_file
        assert self.scalar_definition._source_line

        lineno = self.scalar_definition._source_line

        path = Path(self.scalar_definition._source_file)
        full_source = path.read_text()

        module = cst.parse_module(full_source)
        _metadata_wrapper = MetadataWrapper(module)
        _position_metadata = _metadata_wrapper.resolve(PositionProvider)
        _parent_metadata = _metadata_wrapper.resolve(ParentNodeProvider)

        function_calls = m.findall(
            _metadata_wrapper,
            m.Call(func=m.Attribute(attr=m.Name("scalar")))
            | m.Call(func=m.Name("scalar")),
        )

        call_position = None
        call: Optional[cst.Call] = None

        for function_call in function_calls:
            position = _position_metadata[function_call]

            if position.start.line <= lineno <= position.end.line:
                call_position = position
                call = cast(cst.Call, function_call)

                break

        assert call_position is not None
        assert call is not None

        parent = _parent_metadata[call]
        parent_position = _position_metadata[parent]

        text = ""

        if isinstance(call.func, cst.Attribute):
            assert isinstance(call.func.value, cst.Name)

            text = f"{call.func.value.value}.{call.func.attr.value}"

        if isinstance(call.func, cst.Name):
            assert isinstance(call.func.value, str)

            text = call.func.value

        return ExceptionSource(
            path=path,
            code=full_source,
            start_line=parent_position.start.line,
            end_line=call_position.end.line,
            error_line=parent_position.start.line,
            error_column=parent_position.start.column,
            error_column_end=call_position.start.column + len(text),
        )

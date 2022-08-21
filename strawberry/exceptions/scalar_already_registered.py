from pathlib import Path
from typing import Optional

import libcst as cst
import libcst.matchers as m
from libcst.metadata import MetadataWrapper, PositionProvider

from strawberry.custom_scalar import ScalarDefinition

from .exception import StrawberryException
from .exception_source import ExceptionSource


class ScalarAlreadyRegisteredError(StrawberryException):
    # This should use scalar definition
    def __init__(self, scalar_definition: ScalarDefinition):
        self.scalar_definition = scalar_definition

        scalar_name = scalar_definition.name

        self.message = f"Scalar {scalar_name} has already been registered"
        self.rich_message = (
            f"Scalar `[underline]{scalar_name}[/]` has already been registered"
        )
        self.annotation_message = "scalar defined here"
        self.suggestion = (
            "To fix this error you should either rename the scalar, "
            "or reuse the existing one"
        )

        # todo, accept the other scalar definition and show where it was defined

        super().__init__(self.message)

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        assert self.scalar_definition._source_file
        assert self.scalar_definition._source_line

        # a function call for strawberry.scalar (or just scalar)
        # around line no, that has correct name

        lineno = self.scalar_definition._source_line

        path = Path(self.scalar_definition._source_file)
        full_source = path.read_text()

        module = cst.parse_module(full_source)
        _metadata_wrapper = MetadataWrapper(module)
        _position_metadata = _metadata_wrapper.resolve(PositionProvider)

        function_calls = m.findall(
            _metadata_wrapper, m.Call(func=m.Attribute(attr=m.Name("scalar")))
        )

        call_position = None

        for function_call in function_calls:
            position = _position_metadata[function_call]

            print(position.start.line)

            if position.start.line <= lineno <= position.end.line:
                call_position = position

                break

        assert call_position is not None

        return ExceptionSource(
            path=path,
            code=full_source,
            start_line=call_position.start.line,
            end_line=call_position.end.line,
            error_line=call_position.start.line,
            error_column=0,
            error_column_end=10,
        )

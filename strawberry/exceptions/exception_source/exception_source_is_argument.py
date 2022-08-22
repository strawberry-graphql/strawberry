from typing import Callable, Optional, Union

import libcst.matchers as m
from libcst.metadata import CodeRange

from ..utils.getsource import getsourcelines
from .exception_source import ExceptionSource
from .exception_source_is_function import ExceptionSourceIsFunction


class ExceptionSourceIsArgument(ExceptionSourceIsFunction):
    function: Union[Callable, staticmethod, classmethod]
    argument_name: str

    def _find_argument_definition(self, source: str, line: int) -> CodeRange:
        result = self._find_resolver_node(source, line)

        assert result

        function_def = result[0]

        argument_def = m.findall(
            function_def,
            m.Param(name=m.Name(value=self.argument_name)),
        )

        return self.position_metadata[argument_def[0]]

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        exception_source = super().exception_source

        if exception_source is None:
            return None

        full_source = exception_source.path.read_text()

        _, line = getsourcelines(self.function)

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

import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

import libcst as cst
import libcst.matchers as m
from backports.cached_property import cached_property
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider

from ..utils.getsource import getsourcelines
from .exception_source import ExceptionSource


if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver


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

import inspect
from pathlib import Path
from typing import Optional, Type

import libcst as cst
import libcst.matchers as m
from libcst.metadata import MetadataWrapper, PositionProvider

from ..utils.getsource import getsourcelines
from .exception_source import ExceptionSource
from .node_source import NodeSource


class ExceptionSourceIsClass(Exception):
    cls: Type

    def __init__(self, message: str) -> None:
        super().__init__(message)

        source_file = inspect.getsourcefile(self.cls)

        if source_file is not None:
            self.path = Path(source_file)
            self.source = self.path.read_text()
            _, line = getsourcelines(self.cls)

            # TODO: can we find better ways to do this?
            self.class_definition_line = line

            module = cst.parse_module(self.source)
            self._metadata_wrapper = MetadataWrapper(module)
            self._position_metadata = self._metadata_wrapper.resolve(PositionProvider)

    def _find_class_definition(self) -> Optional[NodeSource]:
        class_defs = m.findall(
            self._metadata_wrapper, m.ClassDef(name=m.Name(value=self.cls.__name__))
        )

        for definition in class_defs:
            position = self._position_metadata[definition]

            if position.start.line >= self.class_definition_line:
                return NodeSource(position, definition)

        return None

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None

        class_def = self._find_class_definition()

        if class_def is None:
            return None

        column_start = class_def.position.start.column + len("class ")

        return ExceptionSource(
            path=self.path,
            code=self.source,
            start_line=class_def.position.start.line,
            error_line=class_def.position.start.line,
            end_line=class_def.position.end.line,
            error_column=column_start,
            error_column_end=column_start + len(self.cls.__name__),
        )

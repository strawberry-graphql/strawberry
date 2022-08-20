import inspect
from pathlib import Path
from typing import Optional, Type

import libcst as cst
import libcst.matchers as m
from libcst.metadata import MetadataWrapper, PositionProvider

from ..utils.getsource import getsourcelines
from .exception_source import ExceptionSource
from .node_source import NodeSource


class ExceptionSourceIsAttribute(Exception):
    cls: Type
    field_name: str

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

    def _find_attribute_in_class(self, class_def: cst.CSTNode) -> Optional[NodeSource]:
        attribute_definition = m.findall(
            class_def,
            m.AssignTarget(target=m.Name(value=self.field_name))
            | m.AnnAssign(target=m.Name(value=self.field_name)),
        )[0]

        if isinstance(attribute_definition, cst.AnnAssign):
            attribute_definition = attribute_definition.target

        return NodeSource(
            self._position_metadata[attribute_definition], attribute_definition
        )

    @property
    def exception_source(self) -> Optional[ExceptionSource]:
        if self.cls is None:
            return None

        class_def_source = self._find_class_definition()

        assert class_def_source

        node_source = self._find_attribute_in_class(class_def_source.node)

        if node_source is None:
            return None

        return ExceptionSource(
            path=self.path,
            code=self.source,
            start_line=class_def_source.position.start.line,
            error_line=node_source.position.start.line,
            end_line=class_def_source.position.end.line,
            error_column=node_source.position.start.column,
            error_column_end=node_source.position.end.column,
        )

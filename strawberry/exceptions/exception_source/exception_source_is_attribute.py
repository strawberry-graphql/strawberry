import inspect
from pathlib import Path
from typing import Optional, Type

import libcst as cst
import libcst.matchers as m
from backports.cached_property import cached_property
from libcst.metadata import MetadataWrapper, PositionProvider

from ..utils.getsource import getsourcelines
from .exception_source import ExceptionSource
from .node_source import NodeSource


class ExceptionSourceIsAttribute:
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

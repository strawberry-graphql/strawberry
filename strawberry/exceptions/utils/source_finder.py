import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Type

from strawberry.utils.cached_property import cached_property

from ..exception_source import ExceptionSource


@dataclass
class SourcePath:
    path: Path
    code: str


class LibCSTSourceFinder:
    def __init__(self) -> None:
        self.cst = importlib.import_module("libcst")

    def find_source(self, module: str) -> Optional[SourcePath]:
        # todo: support for pyodide

        source_module = sys.modules.get(module)

        if source_module is None or source_module.__file__ is None:
            return None

        path = Path(source_module.__file__)

        if not path.exists() or path.suffix != ".py":
            return None

        source = path.read_text()

        return SourcePath(path=path, code=source)

    def find_class(self, cls: Type) -> Optional[ExceptionSource]:
        if self.cst is None:
            return None

        from libcst.metadata import (
            MetadataWrapper,
            ParentNodeProvider,
            PositionProvider,
        )

        source = self.find_source(cls.__module__)

        if source is None:
            return None

        module = self.cst.parse_module(source.code)
        _metadata_wrapper = MetadataWrapper(module)
        _position_metadata = _metadata_wrapper.resolve(PositionProvider)
        _parent_metadata = _metadata_wrapper.resolve(ParentNodeProvider)

        import libcst.matchers as m
        from libcst import ClassDef, CSTNode, FunctionDef

        class_defs = m.findall(
            _metadata_wrapper, m.ClassDef(name=m.Name(value=cls.__name__))
        )

        for definition in class_defs:
            position = _position_metadata[definition]
            parent: Optional[CSTNode] = definition
            stack = []

            while parent:
                if isinstance(parent, ClassDef):
                    stack.append(parent.name.value)

                if isinstance(parent, FunctionDef):
                    stack.extend(("<locals>", parent.name.value))

                parent = _parent_metadata.get(parent)

            found_class_name = ".".join(reversed(stack))

            if found_class_name == cls.__qualname__:
                column_start = position.start.column + len("class ")

                return ExceptionSource(
                    path=source.path,
                    code=source.code,
                    start_line=position.start.line,
                    error_line=position.start.line,
                    end_line=position.end.line,
                    error_column=column_start,
                    error_column_end=column_start + len(cls.__name__),
                )

        return None


class SourceFinder:
    # this might need to become a getter
    @cached_property
    def cst(self) -> Optional[LibCSTSourceFinder]:
        try:
            return LibCSTSourceFinder()
        except ImportError:
            return None

    def find_class_from_object(self, cls: Type) -> Optional[ExceptionSource]:
        if self.cst is None:
            return None

        return self.cst.find_class(cls)

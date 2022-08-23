import importlib
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Optional, Type, TypeVar, cast

from strawberry.utils.cached_property import cached_property

from ..exception_source import ExceptionSource
from .getsource import getsourcefile, getsourcelines


if TYPE_CHECKING:
    from libcst import ClassDef, CSTNode, Module
    from libcst.metadata import CodeRange


NodeType = TypeVar("NodeType", bound="CSTNode")


class NodeSource(Generic[NodeType]):
    position: "CodeRange"
    node: NodeType

    def __init__(self, node: NodeType, position: "CodeRange") -> None:
        self.node = node
        self.position = position


class LibCSTSourceFinder:
    def __init__(self) -> None:
        self.cst = importlib.import_module("libcst")

    def parse_module(self, source: str) -> "Module":
        module = self.cst.parse_module(source)

        # TODO, is this fine?
        from libcst.metadata import MetadataWrapper, PositionProvider

        self._metadata_wrapper = MetadataWrapper(module)
        self._position_metadata = self._metadata_wrapper.resolve(PositionProvider)

        return module

    def find_class(self, cls: Type, source: str) -> Optional[NodeSource["ClassDef"]]:
        if self.cst is None:
            return None

        # TODO: this is annoying we can maybe just use libcst for this
        # we might need to get the code or some other information from the class
        _, line = getsourcelines(cls)

        import libcst.matchers as m

        self.parse_module(source)

        class_defs = m.findall(
            self._metadata_wrapper, m.ClassDef(name=m.Name(value=cls.__name__))
        )

        for definition in class_defs:
            position = self._position_metadata[definition]

            # todo
            if position.start.line >= line:
                return NodeSource(
                    node=cast("ClassDef", definition),
                    position=position,
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

    # TODO: use path like object, do the trick for pyodide
    def _get_source_file(self, obj: object) -> Path:
        return getsourcefile(obj)

    def find_class_from_object(self, cls: Type) -> Optional[ExceptionSource]:
        if self.cst is None:
            return None

        source_file = self._get_source_file(cls)

        if source_file is None:
            return None

        source = source_file.read_text()

        class_source = self.cst.find_class(cls, source)

        if class_source is None:
            return None

        column_start = class_source.position.start.column + len("class ")

        return ExceptionSource(
            path=source_file,
            code=source,
            start_line=class_source.position.start.line,
            error_line=class_source.position.start.line,
            end_line=class_source.position.end.line,
            error_column=column_start,
            error_column_end=column_start + len(cls.__name__),
        )

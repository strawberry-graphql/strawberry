from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

from strawberry.exceptions.exception_source import ExceptionSource

if TYPE_CHECKING:
    from collections.abc import Sequence
    from inspect import Traceback

    from libcst import BinaryOperation, Call, CSTNode, FunctionDef

    from strawberry.types.scalar import ScalarDefinition
    from strawberry.types.union import StrawberryUnion


@dataclass
class SourcePath:
    path: Path
    code: str


class LibCSTSourceFinder:
    def __init__(self) -> None:
        self.cst = importlib.import_module("libcst")

    def find_source(self, module: str) -> Optional[SourcePath]:
        # TODO: support for pyodide

        source_module = sys.modules.get(module)

        path = None

        if source_module is None:
            spec = importlib.util.find_spec(module)

            if spec is not None and spec.origin is not None:
                path = Path(spec.origin)
        elif source_module.__file__ is not None:
            path = Path(source_module.__file__)

        if path is None:
            return None

        if not path.exists() or path.suffix != ".py":
            return None  # pragma: no cover

        source = path.read_text(encoding="utf-8")

        return SourcePath(path=path, code=source)

    def _find(self, source: str, matcher: Any) -> Sequence[CSTNode]:
        from libcst.metadata import (
            MetadataWrapper,
            ParentNodeProvider,
            PositionProvider,
        )

        module = self.cst.parse_module(source)
        self._metadata_wrapper = MetadataWrapper(module)
        self._position_metadata = self._metadata_wrapper.resolve(PositionProvider)
        self._parent_metadata = self._metadata_wrapper.resolve(ParentNodeProvider)

        import libcst.matchers as m

        return m.findall(self._metadata_wrapper, matcher)

    def _find_definition_by_qualname(
        self, qualname: str, nodes: Sequence[CSTNode]
    ) -> Optional[CSTNode]:
        from libcst import ClassDef, FunctionDef

        for definition in nodes:
            parent: Optional[CSTNode] = definition
            stack = []

            while parent:
                if isinstance(parent, ClassDef):
                    stack.append(parent.name.value)

                if isinstance(parent, FunctionDef):
                    stack.extend(("<locals>", parent.name.value))

                parent = self._parent_metadata.get(parent)

            if stack[0] == "<locals>":
                stack.pop(0)

            found_class_name = ".".join(reversed(stack))

            if found_class_name == qualname:
                return definition

        return None

    def _find_function_definition(
        self, source: SourcePath, function: Callable[..., Any]
    ) -> Optional[FunctionDef]:
        import libcst.matchers as m

        matcher = m.FunctionDef(name=m.Name(value=function.__name__))

        function_defs = self._find(source.code, matcher)

        return cast(
            "FunctionDef",
            self._find_definition_by_qualname(function.__qualname__, function_defs),
        )

    def _find_class_definition(
        self, source: SourcePath, cls: type[Any]
    ) -> Optional[CSTNode]:
        import libcst.matchers as m

        matcher = m.ClassDef(name=m.Name(value=cls.__name__))

        class_defs = self._find(source.code, matcher)
        return self._find_definition_by_qualname(cls.__qualname__, class_defs)

    def find_class(self, cls: type[Any]) -> Optional[ExceptionSource]:
        source = self.find_source(cls.__module__)

        if source is None:
            return None  # pragma: no cover

        class_def = self._find_class_definition(source, cls)

        if class_def is None:
            return None  # pragma: no cover

        position = self._position_metadata[class_def]
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

    def find_class_attribute(
        self, cls: type[Any], attribute_name: str
    ) -> Optional[ExceptionSource]:
        source = self.find_source(cls.__module__)

        if source is None:
            return None  # pragma: no cover

        class_def = self._find_class_definition(source, cls)

        if class_def is None:
            return None  # pragma: no cover

        import libcst.matchers as m
        from libcst import AnnAssign

        attribute_definitions = m.findall(
            class_def,
            m.AssignTarget(target=m.Name(value=attribute_name))
            | m.AnnAssign(target=m.Name(value=attribute_name))
            | m.FunctionDef(name=m.Name(value=attribute_name)),
        )

        if not attribute_definitions:
            return None

        attribute_definition = attribute_definitions[0]

        if isinstance(attribute_definition, AnnAssign):
            attribute_definition = attribute_definition.target

        class_position = self._position_metadata[class_def]
        attribute_position = self._position_metadata[attribute_definition]

        return ExceptionSource(
            path=source.path,
            code=source.code,
            start_line=class_position.start.line,
            error_line=attribute_position.start.line,
            end_line=class_position.end.line,
            error_column=attribute_position.start.column,
            error_column_end=attribute_position.end.column,
        )

    def find_function(self, function: Callable[..., Any]) -> Optional[ExceptionSource]:
        source = self.find_source(function.__module__)

        if source is None:
            return None  # pragma: no cover

        function_def = self._find_function_definition(source, function)

        if function_def is None:
            return None  # pragma: no cover

        position = self._position_metadata[function_def]

        prefix = f"def{function_def.whitespace_after_def.value}"

        if function_def.asynchronous:
            prefix = f"async{function_def.asynchronous.whitespace_after.value}{prefix}"

        function_prefix = len(prefix)
        error_column = position.start.column + function_prefix
        error_column_end = error_column + len(function.__name__)

        return ExceptionSource(
            path=source.path,
            code=source.code,
            start_line=position.start.line,
            error_line=position.start.line,
            end_line=position.end.line,
            error_column=error_column,
            error_column_end=error_column_end,
        )

    def find_argument(
        self, function: Callable[..., Any], argument_name: str
    ) -> Optional[ExceptionSource]:
        source = self.find_source(function.__module__)

        if source is None:
            return None  # pragma: no cover

        function_def = self._find_function_definition(source, function)

        if function_def is None:
            return None  # pragma: no cover

        import libcst.matchers as m

        argument_defs = m.findall(
            function_def,
            m.Param(name=m.Name(value=argument_name)),
        )

        if not argument_defs:
            return None  # pragma: no cover

        argument_def = argument_defs[0]

        function_position = self._position_metadata[function_def]
        position = self._position_metadata[argument_def]

        return ExceptionSource(
            path=source.path,
            code=source.code,
            start_line=function_position.start.line,
            end_line=function_position.end.line,
            error_line=position.start.line,
            error_column=position.start.column,
            error_column_end=position.end.column,
        )

    def find_union_call(
        self, path: Path, union_name: str, invalid_type: object
    ) -> Optional[ExceptionSource]:
        import libcst.matchers as m

        source = path.read_text()

        invalid_type_name = getattr(invalid_type, "__name__", None)

        types_arg_matcher = (
            [
                m.Tuple(
                    elements=[
                        m.ZeroOrMore(),
                        m.Element(value=m.Name(value=invalid_type_name)),
                        m.ZeroOrMore(),
                    ],
                )
                | m.List(
                    elements=[
                        m.ZeroOrMore(),
                        m.Element(value=m.Name(value=invalid_type_name)),
                        m.ZeroOrMore(),
                    ],
                )
            ]
            if invalid_type_name is not None
            else []
        )

        matcher = m.Call(
            func=m.Attribute(
                value=m.Name(value="strawberry"),
                attr=m.Name(value="union"),
            )
            | m.Name(value="union"),
            args=[
                m.Arg(value=m.SimpleString(value=f"'{union_name}'"))
                | m.Arg(value=m.SimpleString(value=f'"{union_name}"')),
                m.Arg(*types_arg_matcher),  # type: ignore
            ],
        )

        union_calls = self._find(source, matcher)

        if not union_calls:
            return None  # pragma: no cover

        union_call = cast("Call", union_calls[0])

        if invalid_type_name:
            invalid_type_nodes = m.findall(
                union_call.args[1],
                m.Element(value=m.Name(value=invalid_type_name)),
            )

            if not invalid_type_nodes:
                return None  # pragma: no cover

            invalid_type_node = invalid_type_nodes[0]
        else:
            invalid_type_node = union_call

        position = self._position_metadata[union_call]
        invalid_type_node_position = self._position_metadata[invalid_type_node]

        return ExceptionSource(
            path=path,
            code=source,
            start_line=position.start.line,
            error_line=invalid_type_node_position.start.line,
            end_line=position.end.line,
            error_column=invalid_type_node_position.start.column,
            error_column_end=invalid_type_node_position.end.column,
        )

    def find_union_merge(
        self, union: StrawberryUnion, other: object, frame: Traceback
    ) -> Optional[ExceptionSource]:
        import libcst.matchers as m

        path = Path(frame.filename)
        source = path.read_text()

        other_name = getattr(other, "__name__", None)

        if other_name is None:
            return None  # pragma: no cover

        matcher = m.BinaryOperation(operator=m.BitOr(), right=m.Name(value=other_name))

        merge_calls = self._find(source, matcher)

        if not merge_calls:
            return None  # pragma: no cover

        merge_call_node = cast("BinaryOperation", merge_calls[0])
        invalid_type_node = merge_call_node.right

        position = self._position_metadata[merge_call_node]
        invalid_type_node_position = self._position_metadata[invalid_type_node]

        return ExceptionSource(
            path=path,
            code=source,
            start_line=position.start.line,
            error_line=invalid_type_node_position.start.line,
            end_line=position.end.line,
            error_column=invalid_type_node_position.start.column,
            error_column_end=invalid_type_node_position.end.column,
        )

    def find_annotated_union(
        self, union_definition: StrawberryUnion, invalid_type: object
    ) -> Optional[ExceptionSource]:
        if union_definition._source_file is None:
            return None

        # find things like Annotated[Union[...], strawberry.union(name="aaa")]

        import libcst.matchers as m

        path = Path(union_definition._source_file)
        source = path.read_text()

        matcher = m.Subscript(
            value=m.Name(value="Annotated"),
            slice=(
                m.SubscriptElement(
                    slice=m.Index(
                        value=m.Subscript(
                            value=m.Name(value="Union"),
                        )
                    )
                ),
                m.SubscriptElement(
                    slice=m.Index(
                        value=m.Call(
                            func=m.Attribute(
                                value=m.Name(value="strawberry"),
                                attr=m.Name(value="union"),
                            ),
                            args=[
                                m.Arg(
                                    value=m.SimpleString(
                                        value=f"'{union_definition.graphql_name}'"
                                    )
                                    | m.SimpleString(
                                        value=f'"{union_definition.graphql_name}"'
                                    )
                                )
                            ],
                        )
                    )
                ),
            ),
        )

        annotated_calls = self._find(source, matcher)
        invalid_type_name = getattr(invalid_type, "__name__", None)

        if hasattr(invalid_type, "_scalar_definition"):
            invalid_type_name = invalid_type._scalar_definition.name

        if annotated_calls:
            annotated_call_node = annotated_calls[0]

            if invalid_type_name:
                invalid_type_nodes = m.findall(
                    annotated_call_node,
                    m.SubscriptElement(slice=m.Index(m.Name(invalid_type_name))),
                )

                if not invalid_type_nodes:
                    return None  # pragma: no cover

                invalid_type_node = invalid_type_nodes[0]
            else:
                invalid_type_node = annotated_call_node
        else:
            matcher = m.Subscript(
                value=m.Name(value="Annotated"),
                slice=(
                    m.SubscriptElement(slice=m.Index(value=m.BinaryOperation())),
                    m.SubscriptElement(
                        slice=m.Index(
                            value=m.Call(
                                func=m.Attribute(
                                    value=m.Name(value="strawberry"),
                                    attr=m.Name(value="union"),
                                ),
                                args=[
                                    m.Arg(
                                        value=m.SimpleString(
                                            value=f"'{union_definition.graphql_name}'"
                                        )
                                        | m.SimpleString(
                                            value=f'"{union_definition.graphql_name}"'
                                        )
                                    )
                                ],
                            )
                        )
                    ),
                ),
            )

            annotated_calls = self._find(source, matcher)

            if not annotated_calls:
                return None

            annotated_call_node = annotated_calls[0]

            if invalid_type_name:
                invalid_type_nodes = m.findall(
                    annotated_call_node,
                    m.BinaryOperation(left=m.Name(invalid_type_name)),
                )

                if not invalid_type_nodes:
                    return None  # pragma: no cover

                invalid_type_node = invalid_type_nodes[0].left  # type: ignore
            else:
                invalid_type_node = annotated_call_node

        position = self._position_metadata[annotated_call_node]
        invalid_type_node_position = self._position_metadata[invalid_type_node]

        return ExceptionSource(
            path=path,
            code=source,
            start_line=position.start.line,
            end_line=position.end.line,
            error_line=invalid_type_node_position.start.line,
            error_column=invalid_type_node_position.start.column,
            error_column_end=invalid_type_node_position.end.column,
        )

    def find_scalar_call(
        self, scalar_definition: ScalarDefinition
    ) -> Optional[ExceptionSource]:
        if scalar_definition._source_file is None:
            return None  # pragma: no cover

        import libcst.matchers as m

        path = Path(scalar_definition._source_file)
        source = path.read_text()

        # Try to find direct strawberry.scalar() calls with name parameter
        direct_matcher = m.Call(
            func=m.Attribute(value=m.Name(value="strawberry"), attr=m.Name("scalar"))
            | m.Name("scalar"),
            args=[
                m.ZeroOrMore(),
                m.Arg(
                    keyword=m.Name(value="name"),
                    value=m.SimpleString(value=f"'{scalar_definition.name}'")
                    | m.SimpleString(value=f'"{scalar_definition.name}"'),
                ),
                m.ZeroOrMore(),
            ],
        )

        direct_calls = self._find(source, direct_matcher)
        if direct_calls:
            return self._create_scalar_exception_source(
                path, source, direct_calls[0], scalar_definition, is_newtype=False
            )

        # Try to find strawberry.scalar() calls with NewType pattern
        newtype_matcher = m.Call(
            func=m.Attribute(value=m.Name(value="strawberry"), attr=m.Name("scalar"))
            | m.Name("scalar"),
            args=[
                m.Arg(
                    value=m.Call(
                        func=m.Name(value="NewType"),
                        args=[
                            m.Arg(
                                value=m.SimpleString(
                                    value=f"'{scalar_definition.name}'"
                                )
                                | m.SimpleString(value=f'"{scalar_definition.name}"'),
                            ),
                            m.ZeroOrMore(),
                        ],
                    )
                ),
                m.ZeroOrMore(),
            ],
        )

        newtype_calls = self._find(source, newtype_matcher)
        if newtype_calls:
            return self._create_scalar_exception_source(
                path, source, newtype_calls[0], scalar_definition, is_newtype=True
            )

        return None  # pragma: no cover

    def _create_scalar_exception_source(
        self,
        path: Path,
        source: str,
        call_node: Any,
        scalar_definition: ScalarDefinition,
        is_newtype: bool,
    ) -> Optional[ExceptionSource]:
        """Helper method to create ExceptionSource for scalar calls."""
        import libcst.matchers as m

        if is_newtype:
            # For NewType pattern, find the string argument within the NewType call
            newtype_nodes = m.findall(call_node, m.Call(func=m.Name(value="NewType")))
            if not newtype_nodes:
                return None  # pragma: no cover

            target_node = newtype_nodes[0]
            string_nodes = m.findall(
                target_node,
                m.SimpleString(value=f"'{scalar_definition.name}'")
                | m.SimpleString(value=f'"{scalar_definition.name}"'),
            )
            if not string_nodes:
                return None  # pragma: no cover

            target_node = string_nodes[0]
        else:
            # For direct calls, find the name argument
            target_nodes = m.findall(call_node, m.Arg(keyword=m.Name(value="name")))
            if not target_nodes:
                return None  # pragma: no cover

            target_node = target_nodes[0]

        position = self._position_metadata[call_node]
        target_position = self._position_metadata[target_node]

        return ExceptionSource(
            path=path,
            code=source,
            start_line=position.start.line,
            end_line=position.end.line,
            error_line=target_position.start.line,
            error_column=target_position.start.column,
            error_column_end=target_position.end.column,
        )


class SourceFinder:
    @cached_property
    def cst(self) -> Optional[LibCSTSourceFinder]:
        try:
            return LibCSTSourceFinder()
        except ImportError:
            return None  # pragma: no cover

    def find_class_from_object(self, cls: type[Any]) -> Optional[ExceptionSource]:
        return self.cst.find_class(cls) if self.cst else None

    def find_class_attribute_from_object(
        self, cls: type[Any], attribute_name: str
    ) -> Optional[ExceptionSource]:
        return self.cst.find_class_attribute(cls, attribute_name) if self.cst else None

    def find_function_from_object(
        self, function: Callable[..., Any]
    ) -> Optional[ExceptionSource]:
        return self.cst.find_function(function) if self.cst else None

    def find_argument_from_object(
        self, function: Callable[..., Any], argument_name: str
    ) -> Optional[ExceptionSource]:
        return self.cst.find_argument(function, argument_name) if self.cst else None

    def find_union_call(
        self, path: Path, union_name: str, invalid_type: object
    ) -> Optional[ExceptionSource]:
        return (
            self.cst.find_union_call(path, union_name, invalid_type)
            if self.cst
            else None
        )

    def find_union_merge(
        self, union: StrawberryUnion, other: object, frame: Traceback
    ) -> Optional[ExceptionSource]:
        return self.cst.find_union_merge(union, other, frame) if self.cst else None

    def find_scalar_call(
        self, scalar_definition: ScalarDefinition
    ) -> Optional[ExceptionSource]:
        return self.cst.find_scalar_call(scalar_definition) if self.cst else None

    def find_annotated_union(
        self, union_definition: StrawberryUnion, invalid_type: object
    ) -> Optional[ExceptionSource]:
        return (
            self.cst.find_annotated_union(union_definition, invalid_type)
            if self.cst
            else None
        )


__all__ = ["SourceFinder"]

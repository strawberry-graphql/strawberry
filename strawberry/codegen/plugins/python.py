from __future__ import annotations

import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from strawberry.codegen import CodegenFile, QueryCodegenPlugin
from strawberry.codegen.query_codegen import _get_deps
from strawberry.codegen.types import (
    GraphQLEnum,
    GraphQLEnumValue,
    GraphQLFragmentType,
    GraphQLList,
    GraphQLNullValue,
    GraphQLObjectType,
    GraphQLOptional,
    GraphQLScalar,
    GraphQLUnion,
)

if TYPE_CHECKING:
    from pathlib import Path

    from strawberry.codegen.types import (
        GraphQLArgumentValue,
        GraphQLField,
        GraphQLOperation,
        GraphQLType,
    )


@dataclass
class PythonType:
    type: str
    module: str | None = None


@dataclass
class SharedFragments:
    """Fragment classes collected across operations, written to `fragments.py`."""

    module: str = "fragments"
    classes: dict[str, str] = field(default_factory=dict)
    definitions: dict[str, str | None] = field(default_factory=dict)
    imports: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    def add(
        self,
        name: str,
        code: str,
        imports: dict[str, set[str]],
        definition: str | None = None,
    ) -> None:
        if (
            self.classes.setdefault(name, code) != code
            or self.definitions.setdefault(name, definition) != definition
        ):
            raise ValueError(f"{name} is defined differently in different operations")

        for module, names in imports.items():
            self.imports[module] |= names

    def render(self) -> str:
        imports = _format_imports(self.imports)
        return (imports + "\n\n" + "\n\n".join(self.classes.values())).strip()


def _format_imports(imports: dict[str, set[str]]) -> str:
    return "\n".join(
        f"from {module} import {', '.join(sorted(names))}"
        for module, names in imports.items()
        if names
    )


class PythonPlugin(QueryCodegenPlugin):
    SCALARS_TO_PYTHON_TYPES: ClassVar[dict[str, PythonType]] = {
        "ID": PythonType("str"),
        "Int": PythonType("int"),
        "String": PythonType("str"),
        "Float": PythonType("float"),
        "Boolean": PythonType("bool"),
        "UUID": PythonType("UUID", "uuid"),
        "Date": PythonType("date", "datetime"),
        "DateTime": PythonType("datetime", "datetime"),
        "Time": PythonType("time", "datetime"),
        "Decimal": PythonType("Decimal", "decimal"),
    }

    def __init__(
        self, query: Path, shared_fragments: SharedFragments | None = None
    ) -> None:
        self.imports: dict[str, set[str]] = defaultdict(set)
        self.shared_fragments = shared_fragments
        self.outfile_name: str = query.with_suffix(".py").name
        self.query = query

    def generate_code(
        self, types: list[GraphQLType], operation: GraphQLOperation
    ) -> list[CodegenFile]:
        shared: list[GraphQLType] = []
        if self.shared_fragments is not None:
            shared = self._split_shared_types(types)
            if (
                shared or self.shared_fragments.classes
            ) and self.outfile_name == f"{self.shared_fragments.module}.py":
                raise ValueError(
                    f"Operation output file {self.outfile_name!r} collides with "
                    "the shared fragments module"
                )
            types = [t for t in types if t not in shared]

        printed_types = list(filter(None, (self._print_type(type) for type in types)))

        if self.shared_fragments is None or not shared:
            files = []
        else:
            shared_file = self._shared_file(shared)
            local_names = {
                t.name
                for t in types
                if not isinstance(t, (GraphQLOptional, GraphQLList))
            }
            used = {
                dep.name
                for root in (*types, operation.type)
                for dep in _get_deps(root)
                if not isinstance(dep, (GraphQLOptional, GraphQLList))
            } - local_names
            if imported := set(self.shared_fragments.classes) & used:
                self.imports[self.shared_fragments.module] |= imported
            files = [shared_file] if self.shared_fragments.classes else []

        imports = self._print_imports()

        code = imports + "\n\n" + "\n\n".join(printed_types)

        return [*files, CodegenFile(self.outfile_name, code.strip())]

    def _split_shared_types(self, types: list[GraphQLType]) -> list[GraphQLType]:
        """Fragment types and everything they depend on."""
        deps = [
            dep
            for t in types
            if isinstance(t, GraphQLFragmentType)
            for dep in _get_deps(t)
        ]
        return [t for t in types if t in deps]

    def _shared_file(self, shared: list[GraphQLType]) -> CodegenFile:
        assert self.shared_fragments is not None
        own_imports, self.imports = self.imports, defaultdict(set)
        printed = [
            (
                t.name,
                self._print_type(t),
                t.definition if isinstance(t, GraphQLFragmentType) else None,
            )
            for t in shared
            if not isinstance(t, (GraphQLOptional, GraphQLList))
        ]
        shared_imports, self.imports = self.imports, own_imports

        for name, code, definition in printed:
            if code:
                self.shared_fragments.add(name, code, shared_imports, definition)

        return CodegenFile(
            f"{self.shared_fragments.module}.py", self.shared_fragments.render()
        )

    def _print_imports(self) -> str:
        return _format_imports(self.imports)

    def _get_type_name(self, type_: GraphQLType) -> str:
        if isinstance(type_, GraphQLOptional):
            self.imports["typing"].add("Optional")

            return f"Optional[{self._get_type_name(type_.of_type)}]"

        if isinstance(type_, GraphQLList):
            return f"list[{self._get_type_name(type_.of_type)}]"

        if isinstance(type_, GraphQLUnion):
            return type_.name

        if isinstance(type_, (GraphQLObjectType, GraphQLEnum)):
            return type_.name

        if (
            isinstance(type_, GraphQLScalar)
            and type_.name in self.SCALARS_TO_PYTHON_TYPES
        ):
            python_type = self.SCALARS_TO_PYTHON_TYPES[type_.name]

            if python_type.module is not None:
                self.imports[python_type.module].add(python_type.type)

            return python_type.type

        return type_.name

    def _print_field(self, field: GraphQLField) -> str:
        name = field.name

        if field.alias:
            name = f"# alias for {field.name}\n{field.alias}"

        default_value = ""
        if field.default_value is not None:
            default_value = f" = {self._print_argument_value(field.default_value)}"
        return f"{name}: {self._get_type_name(field.type)}{default_value}"

    def _print_argument_value(self, argval: GraphQLArgumentValue) -> str:
        if hasattr(argval, "values"):
            if isinstance(argval.values, list):
                return (
                    "["
                    + ", ".join(self._print_argument_value(v) for v in argval.values)
                    + "]"
                )
            if isinstance(argval.values, dict):
                return (
                    "{"
                    + ", ".join(
                        f"{k!r}: {self._print_argument_value(v)}"
                        for k, v in argval.values.items()
                    )
                    + "}"
                )
            raise TypeError(f"Unrecognized values type: {argval}")
        if isinstance(argval, GraphQLEnumValue):
            # This is an enum.  It needs the namespace alongside the name.
            if argval.enum_type is None:
                raise ValueError(
                    "GraphQLEnumValue must have a type for python code gen. {argval}"
                )
            return f"{argval.enum_type}.{argval.name}"
        if isinstance(argval, GraphQLNullValue):
            return "None"
        if not hasattr(argval, "value"):
            raise TypeError(f"Unrecognized values type: {argval}")
        return repr(argval.value)

    def _print_enum_value(self, value: str) -> str:
        return f'{value} = "{value}"'

    def _print_object_type(self, type_: GraphQLObjectType) -> str:
        fields = "\n".join(
            self._print_field(field)
            for field in type_.fields
            if field.name != "__typename"
        )

        indent = 4 * " "
        lines = [
            f"class {type_.name}:",
        ]
        if type_.graphql_typename:
            lines.append(
                textwrap.indent(f"# typename: {type_.graphql_typename}", indent)
            )
        lines.append(textwrap.indent(fields, indent))

        return "\n".join(lines)

    def _print_enum_type(self, type_: GraphQLEnum) -> str:
        self.imports["enum"].add("Enum")
        values = "\n".join(self._print_enum_value(value) for value in type_.values)

        return "\n".join(
            [
                f"class {type_.name}(Enum):",
                textwrap.indent(values, " " * 4),
            ]
        )

    def _print_scalar_type(self, type_: GraphQLScalar) -> str:
        if type_.name in self.SCALARS_TO_PYTHON_TYPES:
            return ""

        assert type_.python_type is not None, (
            f"Scalar type must have a python type: {type_.name}"
        )

        self.imports["typing"].add("NewType")
        return f'{type_.name} = NewType("{type_.name}", {type_.python_type.__name__})'

    def _print_union_type(self, type_: GraphQLUnion) -> str:
        self.imports["typing"].add("Union")
        return f"{type_.name} = Union[{', '.join([t.name for t in type_.types])}]"

    def _print_type(self, type_: GraphQLType) -> str:
        if isinstance(type_, GraphQLUnion):
            return self._print_union_type(type_)

        if isinstance(type_, GraphQLObjectType):
            return self._print_object_type(type_)

        if isinstance(type_, GraphQLEnum):
            return self._print_enum_type(type_)

        if isinstance(type_, GraphQLScalar):
            return self._print_scalar_type(type_)

        raise ValueError(f"Unknown type: {type}")  # pragma: no cover


__all__ = ["PythonPlugin", "SharedFragments"]

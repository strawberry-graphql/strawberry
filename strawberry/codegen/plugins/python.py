from __future__ import annotations

import textwrap
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from strawberry.codegen import CodegenFile, QueryCodegenPlugin
from strawberry.codegen.types import (
    GraphQLEnum,
    GraphQLEnumValue,
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
    module: Optional[str] = None


class PythonPlugin(QueryCodegenPlugin):
    SCALARS_TO_PYTHON_TYPES: Dict[str, PythonType] = {
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

    def __init__(self, query: Path) -> None:
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.outfile_name: str = query.with_suffix(".py").name
        self.query = query

    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> List[CodegenFile]:
        printed_types = list(filter(None, (self._print_type(type) for type in types)))
        imports = self._print_imports()

        code = imports + "\n\n" + "\n\n".join(printed_types)

        return [CodegenFile(self.outfile_name, code.strip())]

    def _print_imports(self) -> str:
        imports = [
            f'from {import_} import {", ".join(sorted(types))}'
            for import_, types in self.imports.items()
        ]

        return "\n".join(imports)

    def _get_type_name(self, type_: GraphQLType) -> str:
        if isinstance(type_, GraphQLOptional):
            self.imports["typing"].add("Optional")

            return f"Optional[{self._get_type_name(type_.of_type)}]"

        if isinstance(type_, GraphQLList):
            self.imports["typing"].add("List")

            return f"List[{self._get_type_name(type_.of_type)}]"

        if isinstance(type_, GraphQLUnion):
            # TODO: wrong place for this
            self.imports["typing"].add("Union")

            return type_.name

        if isinstance(type_, (GraphQLObjectType, GraphQLEnum)):
            if isinstance(type_, GraphQLEnum):
                self.imports["enum"].add("Enum")

            return type_.name

        if (
            isinstance(type_, GraphQLScalar)
            and type_.name in self.SCALARS_TO_PYTHON_TYPES
        ):
            python_type = self.SCALARS_TO_PYTHON_TYPES[type_.name]

            if python_type.module is not None:
                self.imports[python_type.module].add(python_type.type)

            return python_type.type

        self.imports["typing"].add("NewType")

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
            elif isinstance(argval.values, dict):
                return (
                    "{"
                    + ", ".join(
                        f"{k!r}: {self._print_argument_value(v)}"
                        for k, v in argval.values.items()
                    )
                    + "}"
                )
            else:
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

        assert (
            type_.python_type is not None
        ), f"Scalar type must have a python type: {type_.name}"

        return f'{type_.name} = NewType("{type_.name}", {type_.python_type.__name__})'

    def _print_union_type(self, type_: GraphQLUnion) -> str:
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


__all__ = ["PythonPlugin"]

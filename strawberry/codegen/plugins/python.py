import textwrap
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from strawberry.codegen import CodegenFile, QueryCodegenPlugin
from strawberry.codegen.types import (
    GraphQLEnum,
    GraphQLField,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOperation,
    GraphQLOptional,
    GraphQLScalar,
    GraphQLType,
    GraphQLUnion,
)


@dataclass
class PythonType:
    type: str
    module: Optional[str] = None


class PythonPlugin(QueryCodegenPlugin):
    SCALARS_TO_PYTHON_TYPES = {
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

    def __init__(self) -> None:
        self.imports: Dict[str, Set[str]] = defaultdict(set)

    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> List[CodegenFile]:
        printed_types = list(filter(None, (self._print_type(type) for type in types)))
        imports = self._print_imports()

        code = imports + "\n\n" + "\n\n".join(printed_types)

        return [CodegenFile("types.py", code.strip())]

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

        return f"{name}: {self._get_type_name(field.type)}"

    def _print_enum_value(self, value: str) -> str:
        return f'{value} = "{value}"'

    def _print_object_type(self, type_: GraphQLObjectType) -> str:
        fields = "\n".join(self._print_field(field) for field in type_.fields)

        return "\n".join(
            [
                f"class {type_.name}:",
                textwrap.indent(fields, " " * 4),
            ]
        )

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

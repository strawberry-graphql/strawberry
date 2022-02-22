import textwrap
from collections import defaultdict
from typing import Dict, List, Set

from strawberry.codegen import (
    CodegenPlugin,
    GraphQLEnum,
    GraphQLField,
    GraphQLObjectType,
    GraphQLOptional,
    GraphQLScalar,
    GraphQLType,
    GraphQLUnion,
)


class PythonPlugin(CodegenPlugin):
    SCALARS_TO_PYTHON_TYPES = {
        "Int": "int",
        "String": "str",
    }

    def __init__(self) -> None:
        self.imports: Dict[str, Set[str]] = defaultdict(set)

    def print(self, types: List[GraphQLType]) -> str:
        printed_types = (self._print_type(type) for type in types)
        printed_types = filter(None, printed_types)

        imports = self._print_imports()

        return imports + "\n\n" + "\n\n".join(printed_types)

    def _print_imports(self) -> str:
        imports = [
            f'from {import_} import {", ".join(sorted(types))}'
            for import_, types in self.imports.items()
        ]

        return "\n".join(imports)

    def _get_type_name(self, type_: GraphQLType) -> str:
        if isinstance(type_, GraphQLOptional):
            return f"Optional[{self._get_type_name(type_.of_type)}]"

        if isinstance(type_, GraphQLScalar):
            return self.SCALARS_TO_PYTHON_TYPES[type_.name]

        self.imports["typing"].add("NewType")

        return type_.name

    def _print_field(self, field: GraphQLField) -> str:

        return f"{field.name}: {self._get_type_name(field.type)}"

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

        return f'{type_.name} = NewType("{type_.name}", {type_.type})'

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

        raise ValueError(f"Unknown type: {type}")

    def on_union(self) -> None:
        self.imports["typing"].add("Union")

    def on_enum(self) -> None:
        self.imports["enum"].add("Enum")

    def on_optional(self) -> None:
        self.imports["typing"].add("Optional")

    def on_list(self) -> None:
        self.imports["typing"].add("List")

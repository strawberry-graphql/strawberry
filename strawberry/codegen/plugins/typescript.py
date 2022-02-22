import textwrap
from typing import List

from strawberry.codegen import (
    CodegenPlugin,
    GraphQLEnum,
    GraphQLField,
    GraphQLObjectType,
    GraphQLScalar,
    GraphQLType,
)


class TypeScriptPlugin(CodegenPlugin):
    def print(self, types: List[GraphQLType]) -> str:
        return "\n\n".join(self._print_type(type) for type in types)

    def _print_field(self, field: GraphQLField) -> str:
        return f"{field.name}: {field.type}"

    def _print_enum_value(self, value: str) -> str:
        return f'{value} = "{value}"'

    def _print_object_type(self, type_: GraphQLObjectType) -> str:
        fields = "\n".join(self._print_field(field) for field in type_.fields)

        return "\n".join(
            [
                f"type {type_.name} = {{",
                textwrap.indent(fields, " " * 4),
                "}",
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
        return f'{type_.name} = NewType("{type_.name}", {type_.type})'

    def _print_type(self, type_: GraphQLType) -> str:
        if isinstance(type_, GraphQLObjectType):
            return self._print_object_type(type_)

        if isinstance(type_, GraphQLEnum):
            return self._print_enum_type(type_)

        if isinstance(type_, GraphQLScalar):
            return self._print_scalar_type(type_)

        raise ValueError(f"Unknown type: {type}")

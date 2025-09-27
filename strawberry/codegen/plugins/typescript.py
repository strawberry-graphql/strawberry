from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, ClassVar

from strawberry.codegen import CodegenFile, QueryCodegenPlugin
from strawberry.codegen.types import (
    GraphQLEnum,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOptional,
    GraphQLScalar,
    GraphQLUnion,
)

if TYPE_CHECKING:
    from pathlib import Path

    from strawberry.codegen.types import GraphQLField, GraphQLOperation, GraphQLType


class TypeScriptPlugin(QueryCodegenPlugin):
    SCALARS_TO_TS_TYPE: ClassVar[dict[str | type, str]] = {
        "ID": "string",
        "Int": "number",
        "String": "string",
        "Float": "number",
        "Boolean": "boolean",
        "UUID": "string",
        "Date": "string",
        "DateTime": "string",
        "Time": "string",
        "Decimal": "string",
        str: "string",
        float: "number",
    }

    def __init__(self, query: Path) -> None:
        self.outfile_name: str = query.with_suffix(".ts").name
        self.query = query

    def generate_code(
        self, types: list[GraphQLType], operation: GraphQLOperation
    ) -> list[CodegenFile]:
        printed_types = list(filter(None, (self._print_type(type) for type in types)))

        return [CodegenFile(self.outfile_name, "\n\n".join(printed_types))]

    def _get_type_name(self, type_: GraphQLType) -> str:
        if isinstance(type_, GraphQLOptional):
            return f"{self._get_type_name(type_.of_type)} | undefined"

        if isinstance(type_, GraphQLList):
            child_type = self._get_type_name(type_.of_type)

            if "|" in child_type:
                child_type = f"({child_type})"

            return f"{child_type}[]"

        if isinstance(type_, GraphQLUnion):
            return type_.name

        if isinstance(type_, (GraphQLObjectType, GraphQLEnum)):
            return type_.name

        if isinstance(type_, GraphQLScalar) and type_.name in self.SCALARS_TO_TS_TYPE:
            return self.SCALARS_TO_TS_TYPE[type_.name]

        return type_.name

    def _print_field(self, field: GraphQLField) -> str:
        name = field.name

        if field.alias:
            name = f"// alias for {field.name}\n{field.alias}"

        return f"{name}: {self._get_type_name(field.type)}"

    def _print_oneof_field(self, field: GraphQLField) -> str:
        name = field.name

        if isinstance(field.type, GraphQLOptional):
            # Use the non-null version of the type because we're using unions instead
            output_type = field.type.of_type
        else:
            # Shouldn't run, oneOf types are always nullable
            # Keeping it here just in case
            output_type = field.type  # pragma: no cover
        return f"{name}: {self._get_type_name(output_type)}"

    def _print_enum_value(self, value: str) -> str:
        return f'{value} = "{value}",'

    def _print_object_type(self, type_: GraphQLObjectType) -> str:
        fields = "\n".join(self._print_field(field) for field in type_.fields)

        return "\n".join(
            [f"type {type_.name} = {{", textwrap.indent(fields, " " * 4), "}"],
        )

    def _print_oneof_object_type(self, type_: GraphQLObjectType) -> str:
        # We'll gather a list of objects for each oneOf field
        options: list[str] = []
        for option in type_.fields:
            # We'll give each option all fields from the parent type
            option_fields: list[str] = []
            for field in type_.fields:
                if field == option:
                    # Each option gets one field with its type...
                    field_row = self._print_oneof_field(field)
                else:
                    # ... and the rest set to `never` to prevent multiple from being set
                    field_row = f"{field.name}?: never"
                option_fields.append(field_row)
            options.append("{ " + ", ".join(option_fields) + " }")

        # Union all the options together
        all_options = "\n    | ".join(options)

        return f"type {type_.name} = {all_options}"

    def _print_enum_type(self, type_: GraphQLEnum) -> str:
        values = "\n".join(self._print_enum_value(value) for value in type_.values)

        return "\n".join(
            [
                f"enum {type_.name} {{",
                textwrap.indent(values, " " * 4),
                "}",
            ]
        )

    def _print_scalar_type(self, type_: GraphQLScalar) -> str:
        if type_.name in self.SCALARS_TO_TS_TYPE:
            return ""

        assert type_.python_type is not None
        return f"type {type_.name} = {self.SCALARS_TO_TS_TYPE[type_.python_type]}"

    def _print_union_type(self, type_: GraphQLUnion) -> str:
        return f"type {type_.name} = {' | '.join([t.name for t in type_.types])}"

    def _print_type(self, type_: GraphQLType) -> str:
        if isinstance(type_, GraphQLUnion):
            return self._print_union_type(type_)

        if isinstance(type_, GraphQLObjectType):
            if type_.is_one_of:
                return self._print_oneof_object_type(type_)
            else:
                return self._print_object_type(type_)

        if isinstance(type_, GraphQLEnum):
            return self._print_enum_type(type_)

        if isinstance(type_, GraphQLScalar):
            return self._print_scalar_type(type_)

        raise ValueError(f"Unknown type: {type}")  # pragma: no cover

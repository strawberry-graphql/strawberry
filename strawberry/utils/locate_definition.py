from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry.exceptions.utils.source_finder import SourceFinder
from strawberry.types.scalar import ScalarDefinition
from strawberry.types.union import StrawberryUnion
from strawberry.utils.str_converters import to_snake_case

if TYPE_CHECKING:
    from strawberry.schema.schema import Schema


def locate_definition(schema_symbol: Schema, symbol: str) -> str | None:
    finder = SourceFinder()

    if "." in symbol:
        model, field = symbol.split(".", 1)
    else:
        model, field = symbol, None

    schema_type = schema_symbol.get_type_by_name(model)

    if not schema_type:
        return None

    if field:
        assert not isinstance(schema_type, StrawberryUnion)

        location = finder.find_class_attribute_from_object(
            schema_type.origin,  # type: ignore
            to_snake_case(field)
            if schema_symbol.config.name_converter.auto_camel_case
            else field,
        )
    elif isinstance(schema_type, StrawberryUnion):
        location = finder.find_annotated_union(schema_type, None)
    elif isinstance(schema_type, ScalarDefinition):
        location = finder.find_scalar_call(schema_type)
    else:
        location = finder.find_class_from_object(schema_type.origin)

    if not location:
        return None

    return f"{location.path}:{location.error_line}:{location.error_column + 1}"

from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry.exceptions.utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.schema.schema import Schema


def locate_definition(schema_symbol: Schema, symbol: str) -> str | None:
    finder = SourceFinder()

    if "." in symbol:
        model, field = symbol.split(".")
    else:
        model, field = symbol, None

    schema_type = schema_symbol.get_type_by_name(model)

    if not schema_type:
        return None

    location = (
        finder.find_class_attribute_from_object(schema_type.origin, field)
        if field
        else finder.find_class_from_object(schema_type.origin)
    )

    if not location:
        return None

    return f"{location.path}:{location.error_line}:{location.error_column + 1}"

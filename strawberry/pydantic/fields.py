"""Field processing utilities for Pydantic models in Strawberry GraphQL.

This module provides functions to extract and process fields from Pydantic BaseModel
classes, converting them to StrawberryField instances that can be used in GraphQL schemas.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from strawberry.annotation import StrawberryAnnotation
from strawberry.experimental.pydantic._compat import PydanticCompat
from strawberry.experimental.pydantic.fields import replace_types_recursively
from strawberry.experimental.pydantic.utils import get_default_factory_for_field
from strawberry.types.field import StrawberryField
from strawberry.types.private import is_private

if TYPE_CHECKING:
    from pydantic import BaseModel


def get_type_for_field(field, is_input: bool, compat: PydanticCompat):
    """Get the GraphQL type for a Pydantic field."""
    outer_type = field.outer_type_

    replaced_type = replace_types_recursively(outer_type, is_input, compat=compat)

    if field.is_v1:
        # only pydantic v1 has this Optional logic
        should_add_optional: bool = field.allow_none
        if should_add_optional:
            from typing import Optional
            return Optional[replaced_type]

    return replaced_type


def _get_pydantic_fields(
    cls: type[BaseModel],
    original_type_annotations: dict[str, type[Any]],
    is_input: bool = False,
    fields_set: set[str] | None = None,
    auto_fields_set: set[str] | None = None,
    use_pydantic_alias: bool = True,
    include_computed: bool = False,
) -> list[StrawberryField]:
    """Extract StrawberryFields from a Pydantic BaseModel class.
    
    This function processes a Pydantic BaseModel and extracts its fields,
    converting them to StrawberryField instances that can be used in GraphQL schemas.
    
    Args:
        cls: The Pydantic BaseModel class to extract fields from
        original_type_annotations: Type annotations that may override field types
        is_input: Whether this is for an input type
        fields_set: Set of field names to include (None means all fields)
        auto_fields_set: Set of field names marked with strawberry.auto
        use_pydantic_alias: Whether to use Pydantic field aliases
        include_computed: Whether to include computed fields
        
    Returns:
        List of StrawberryField instances
    """
    fields: list[StrawberryField] = []

    # Get compatibility layer for this model
    compat = PydanticCompat.from_model(cls)

    # Extract Pydantic model fields
    model_fields = compat.get_model_fields(cls, include_computed=include_computed)

    # Get annotations from the class to check for strawberry.auto and custom fields
    existing_annotations = getattr(cls, "__annotations__", {})

    # If no fields_set specified, use all model fields
    if fields_set is None:
        fields_set = set(model_fields.keys())

    # If no auto_fields_set specified, use empty set (no auto fields in direct integration)
    if auto_fields_set is None:
        auto_fields_set = set()

    # Process each field that should be included
    for field_name in fields_set:
        # Check if this field exists in the Pydantic model
        if field_name not in model_fields:
            continue

        pydantic_field = model_fields[field_name]

        # Check if this is a private field
        field_type = (
            get_type_for_field(pydantic_field, is_input, compat=compat)
            if field_name in auto_fields_set
            else existing_annotations.get(field_name)
        )

        if field_type and is_private(field_type):
            continue

        # Get the appropriate field type
        if field_name in auto_fields_set:
            # This is a field that should use the Pydantic type (for all_fields=True)
            field_type = get_type_for_field(pydantic_field, is_input, compat=compat)
        else:
            # This must be a custom field, skip processing the Pydantic field
            continue

        # Check if there's a custom field definition on the class
        custom_field = getattr(cls, field_name, None)
        if isinstance(custom_field, StrawberryField):
            # Use the custom field but update its type if needed
            strawberry_field = custom_field
            if field_name in auto_fields_set:
                strawberry_field.type_annotation = StrawberryAnnotation.from_annotation(field_type)
        else:
            # Create a new StrawberryField
            graphql_name = None
            if pydantic_field.has_alias and use_pydantic_alias:
                graphql_name = pydantic_field.alias

            strawberry_field = StrawberryField(
                python_name=field_name,
                graphql_name=graphql_name,
                type_annotation=StrawberryAnnotation.from_annotation(field_type),
                description=pydantic_field.description,
                default_factory=get_default_factory_for_field(pydantic_field, compat=compat),
            )

        # Set the origin module for proper type resolution
        origin = cls
        module = sys.modules[origin.__module__]

        if (
            isinstance(strawberry_field.type_annotation, StrawberryAnnotation)
            and strawberry_field.type_annotation.namespace is None
        ):
            strawberry_field.type_annotation.namespace = module.__dict__

        strawberry_field.origin = origin

        # Apply any type overrides from original_type_annotations
        if field_name in original_type_annotations:
            strawberry_field.type = original_type_annotations[field_name]
            strawberry_field.type_annotation = StrawberryAnnotation(
                annotation=strawberry_field.type
            )

        fields.append(strawberry_field)

    return fields


__all__ = ["_get_pydantic_fields", "get_type_for_field"]

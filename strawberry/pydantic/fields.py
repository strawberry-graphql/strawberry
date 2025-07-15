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
    include_computed: bool = False,
) -> list[StrawberryField]:
    """Extract StrawberryFields from a Pydantic BaseModel class.
    
    This function processes a Pydantic BaseModel and extracts its fields,
    converting them to StrawberryField instances that can be used in GraphQL schemas.
    All fields from the Pydantic model are included by default, except those marked
    with strawberry.Private.
    
    Args:
        cls: The Pydantic BaseModel class to extract fields from
        original_type_annotations: Type annotations that may override field types
        is_input: Whether this is for an input type
        include_computed: Whether to include computed fields
        
    Returns:
        List of StrawberryField instances
    """
    fields: list[StrawberryField] = []

    # Get compatibility layer for this model
    compat = PydanticCompat.from_model(cls)

    # Extract Pydantic model fields
    model_fields = compat.get_model_fields(cls, include_computed=include_computed)

    # Get annotations from the class to check for strawberry.Private and other custom fields
    existing_annotations = getattr(cls, "__annotations__", {})

    # Process each field from the Pydantic model
    for field_name, pydantic_field in model_fields.items():
        # Check if this field is marked as private
        if field_name in existing_annotations:
            field_type = existing_annotations[field_name]
            # Skip private fields - they shouldn't be included in GraphQL schema
            if is_private(field_type):
                continue

        # Get the field type from the Pydantic model
        field_type = get_type_for_field(pydantic_field, is_input, compat=compat)

        # Check if there's a custom field definition on the class
        custom_field = getattr(cls, field_name, None)
        if isinstance(custom_field, StrawberryField):
            # Use the custom field but update its type if needed
            strawberry_field = custom_field
            strawberry_field.type_annotation = StrawberryAnnotation.from_annotation(field_type)
        else:
            # Create a new StrawberryField
            graphql_name = None
            if pydantic_field.has_alias:
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


__all__ = ["_get_pydantic_fields"]

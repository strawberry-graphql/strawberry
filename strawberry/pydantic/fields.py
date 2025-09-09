"""Field processing utilities for Pydantic models in Strawberry GraphQL.

This module provides functions to extract and process fields from Pydantic BaseModel
classes, converting them to StrawberryField instances that can be used in GraphQL schemas.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, get_args, get_origin
from typing import Union as TypingUnion
from typing import _GenericAlias as TypingGenericAlias

from strawberry.annotation import StrawberryAnnotation
from strawberry.experimental.pydantic._compat import PydanticCompat
from strawberry.experimental.pydantic.utils import get_default_factory_for_field
from strawberry.types.field import StrawberryField
from strawberry.types.private import is_private
from strawberry.utils.typing import is_union

from .exceptions import UnregisteredTypeException

if TYPE_CHECKING:
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo

from strawberry.experimental.pydantic._compat import lenient_issubclass


def _extract_strawberry_field_from_annotation(
    annotation: Any,
) -> StrawberryField | None:
    """Extract StrawberryField from an Annotated type annotation.

    Args:
        annotation: The type annotation, possibly Annotated[Type, strawberry.field(...)]

    Returns:
        StrawberryField instance if found in annotation metadata, None otherwise
    """
    # Check if this is an Annotated type
    if hasattr(annotation, "__metadata__"):
        # Look for StrawberryField in the metadata
        for metadata_item in annotation.__metadata__:
            if isinstance(metadata_item, StrawberryField):
                return metadata_item

    return None


def replace_pydantic_types(type_: Any, is_input: bool) -> Any:
    """Replace Pydantic types with their Strawberry equivalents for first-class integration."""
    from pydantic import BaseModel

    if lenient_issubclass(type_, BaseModel):
        if hasattr(type_, "__strawberry_definition__"):
            return type_

        raise UnregisteredTypeException(type_)

    return type_


def replace_types_recursively(
    type_: Any,
    is_input: bool,
    compat: PydanticCompat,
) -> Any:
    """Recursively replace Pydantic types with their Strawberry equivalents."""
    # For now, use a simpler approach similar to the experimental module
    basic_type = compat.get_basic_type(type_)
    replaced_type = replace_pydantic_types(basic_type, is_input)

    origin = get_origin(type_)

    if not origin or not hasattr(type_, "__args__"):
        return replaced_type

    converted = tuple(
        replace_types_recursively(t, is_input=is_input, compat=compat)
        for t in get_args(replaced_type)
    )

    # Handle special cases for typing generics
    if isinstance(replaced_type, TypingGenericAlias):
        return TypingGenericAlias(origin, converted)
    if is_union(replaced_type):
        return TypingUnion[converted]

    # Fallback to origin[converted] for standard generic types
    return origin[converted]


def get_type_for_field(field: FieldInfo, is_input: bool, compat: PydanticCompat) -> Any:
    """Get the GraphQL type for a Pydantic field."""
    return replace_types_recursively(field.outer_type_, is_input, compat=compat)


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

    Fields can be customized using strawberry.field() overrides:

    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: int = strawberry.field(directives=[SomeDirective()])

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

    # Get annotations from the class to check for strawberry.Private and strawberry.field() overrides
    existing_annotations = getattr(cls, "__annotations__", {})

    # Process each field from the Pydantic model
    for field_name, pydantic_field in model_fields.items():
        # Check if this field is marked as private or has strawberry.field() metadata
        strawberry_override = None
        if field_name in existing_annotations:
            field_annotation = existing_annotations[field_name]

            # Skip private fields - they shouldn't be included in GraphQL schema
            if is_private(field_annotation):
                continue

            # Check for strawberry.field() in Annotated metadata
            strawberry_override = _extract_strawberry_field_from_annotation(
                field_annotation
            )

        # Get the field type from the Pydantic model
        field_type = get_type_for_field(pydantic_field, is_input, compat=compat)

        # Start with values from Pydantic field
        graphql_name = pydantic_field.alias if pydantic_field.has_alias else None
        description = pydantic_field.description
        directives = []
        permission_classes = []
        extensions = []
        deprecation_reason = None

        # If there's a strawberry.field() override, merge its values
        if strawberry_override:
            # strawberry.field() overrides take precedence for GraphQL-specific settings
            if strawberry_override.graphql_name is not None:
                graphql_name = strawberry_override.graphql_name
            if strawberry_override.description is not None:
                description = strawberry_override.description
            if strawberry_override.directives:
                directives = list(strawberry_override.directives)
            if strawberry_override.permission_classes:
                permission_classes = list(strawberry_override.permission_classes)
            if strawberry_override.extensions:
                extensions = list(strawberry_override.extensions)
            if strawberry_override.deprecation_reason is not None:
                deprecation_reason = strawberry_override.deprecation_reason

        strawberry_field = StrawberryField(
            python_name=field_name,
            graphql_name=graphql_name,
            type_annotation=StrawberryAnnotation.from_annotation(field_type),
            description=description,
            default_factory=get_default_factory_for_field(
                pydantic_field, compat=compat
            ),
            directives=directives,
            permission_classes=permission_classes,
            extensions=extensions,
            deprecation_reason=deprecation_reason,
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

        fields.append(strawberry_field)

    return fields


__all__ = [
    "_get_pydantic_fields",
    "replace_pydantic_types",
    "replace_types_recursively",
]

"""Native Strawberry type map for fast type and field lookups without GraphQL Core.

This module provides a type registry that:
1. Maps GraphQL names to Strawberry types
2. Pre-computes all name conversions (snake_case <-> camelCase)
3. Provides O(1) field lookups by GraphQL or Python names
4. Eliminates repeated name conversions during query execution
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphql import GraphQLSchema

    from strawberry.schema.config import StrawberryConfig
    from strawberry.types.field import StrawberryField
    from strawberry.types.types import StrawberryObjectDefinition


class FieldMap:
    """Bidirectional field mapping for fast lookups by either GraphQL or Python name."""

    def __init__(self):
        self.by_graphql_name: dict[str, StrawberryField] = {}
        self.by_python_name: dict[str, StrawberryField] = {}
        # Store the name mappings for quick access
        self.graphql_to_python: dict[str, str] = {}
        self.python_to_graphql: dict[str, str] = {}

    def add_field(self, graphql_name: str, python_name: str, field: StrawberryField):
        """Add a field with both its GraphQL and Python names."""
        self.by_graphql_name[graphql_name] = field
        self.by_python_name[python_name] = field
        self.graphql_to_python[graphql_name] = python_name
        self.python_to_graphql[python_name] = graphql_name

        # Store names directly on the field for quick access
        field.graphql_name = graphql_name
        field.python_name = python_name

    def get_by_graphql_name(self, name: str) -> StrawberryField | None:
        """Get field by its GraphQL name (e.g., 'authorName')."""
        return self.by_graphql_name.get(name)

    def get_by_python_name(self, name: str) -> StrawberryField | None:
        """Get field by its Python name (e.g., 'author_name')."""
        return self.by_python_name.get(name)

    def get_python_name(self, graphql_name: str) -> str | None:
        """Convert GraphQL name to Python name."""
        return self.graphql_to_python.get(graphql_name)

    def get_graphql_name(self, python_name: str) -> str | None:
        """Convert Python name to GraphQL name."""
        return self.python_to_graphql.get(python_name)


class StrawberryTypeMap:
    """Native type registry for Strawberry schemas.

    This provides fast access to Strawberry types and fields without
    going through GraphQL Core, with pre-computed name conversions.
    """

    def __init__(self, config: StrawberryConfig):
        self.config = config
        self.types: dict[str, StrawberryObjectDefinition] = {}
        self.field_maps: dict[str, FieldMap] = {}

        # Store root types for quick access
        self.query_type: StrawberryObjectDefinition | None = None
        self.mutation_type: StrawberryObjectDefinition | None = None
        self.subscription_type: StrawberryObjectDefinition | None = None

    def build_from_schema(self, graphql_schema: GraphQLSchema):
        """Build the type map from a GraphQL schema.

        This extracts Strawberry types from the GraphQL schema and
        pre-computes all name conversions.
        """
        from strawberry.schema.schema_converter import GraphQLCoreConverter

        # Iterate through all types in the GraphQL schema
        for type_name, graphql_type in graphql_schema.type_map.items():
            # Skip introspection types
            if type_name.startswith("__"):
                continue

            # Get the Strawberry type from extensions
            if hasattr(graphql_type, "extensions") and graphql_type.extensions:
                strawberry_type = graphql_type.extensions.get(
                    GraphQLCoreConverter.DEFINITION_BACKREF
                )

                if strawberry_type:
                    self.types[type_name] = strawberry_type

                    # Store the GraphQL name on the type
                    strawberry_type.graphql_name = type_name

                    # Build field map for object types
                    if hasattr(graphql_type, "fields"):
                        field_map = FieldMap()

                        for field_name, graphql_field in graphql_type.fields.items():
                            if (
                                hasattr(graphql_field, "extensions")
                                and graphql_field.extensions
                            ):
                                strawberry_field = graphql_field.extensions.get(
                                    GraphQLCoreConverter.DEFINITION_BACKREF
                                )

                                if strawberry_field:
                                    # Get the Python name from the StrawberryField
                                    python_name = (
                                        strawberry_field.python_name or field_name
                                    )

                                    # Add to field map with both names
                                    field_map.add_field(
                                        field_name,  # GraphQL name
                                        python_name,  # Python name
                                        strawberry_field,
                                    )

                        self.field_maps[type_name] = field_map

                        # Store field map on the type itself for direct access
                        strawberry_type._field_map = field_map

        # Store root types
        if graphql_schema.query_type:
            self.query_type = self.types.get(graphql_schema.query_type.name)
        if graphql_schema.mutation_type:
            self.mutation_type = self.types.get(graphql_schema.mutation_type.name)
        if graphql_schema.subscription_type:
            self.subscription_type = self.types.get(
                graphql_schema.subscription_type.name
            )

    def get_type(self, graphql_name: str) -> StrawberryObjectDefinition | None:
        """Get a type by its GraphQL name."""
        return self.types.get(graphql_name)

    def get_field(self, type_name: str, field_name: str) -> StrawberryField | None:
        """Get a field by type name and field name (both GraphQL names)."""
        field_map = self.field_maps.get(type_name)
        if field_map:
            return field_map.get_by_graphql_name(field_name)
        return None

    def get_field_by_python_name(
        self, type_name: str, python_field_name: str
    ) -> StrawberryField | None:
        """Get a field by type name (GraphQL) and Python field name."""
        field_map = self.field_maps.get(type_name)
        if field_map:
            return field_map.get_by_python_name(python_field_name)
        return None

    def convert_field_name(self, type_name: str, graphql_field_name: str) -> str | None:
        """Convert a GraphQL field name to Python name for a given type."""
        field_map = self.field_maps.get(type_name)
        if field_map:
            return field_map.get_python_name(graphql_field_name)
        return None

    def has_type(self, graphql_name: str) -> bool:
        """Check if a type exists by GraphQL name."""
        return graphql_name in self.types

    def has_field(self, type_name: str, field_name: str) -> bool:
        """Check if a field exists (both names are GraphQL names)."""
        field_map = self.field_maps.get(type_name)
        return field_map is not None and field_name in field_map.by_graphql_name

    def get_field_resolver(self, type_name: str, field_name: str):
        """Get the resolver function for a field (if any)."""
        field = self.get_field(type_name, field_name)
        if field and field.base_resolver:
            return field.base_resolver.wrapped_func
        return None

    def is_field_async(self, type_name: str, field_name: str) -> bool:
        """Check if a field is async."""
        field = self.get_field(type_name, field_name)
        if field:
            return field.is_async
        return False

    def get_field_arguments(self, type_name: str, field_name: str):
        """Get the arguments for a field."""
        field = self.get_field(type_name, field_name)
        if field:
            return field.arguments
        return []

    def __repr__(self) -> str:
        return (
            f"<StrawberryTypeMap types={len(self.types)} "
            f"query={self.query_type is not None} "
            f"mutation={self.mutation_type is not None} "
            f"subscription={self.subscription_type is not None}>"
        )

from typing import Callable, Optional, Type, Union, cast

from graphql import GraphQLList, GraphQLNonNull, GraphQLType

from strawberry.field import FieldDefinition
from strawberry.scalars import is_scalar
from strawberry.types.types import ArgumentDefinition
from strawberry.union import StrawberryUnion

from .enum import get_enum_type
from .scalar import get_scalar_type
from .types import TypeMap
from .union import get_union_type


def get_type_for_annotation(annotation: Type, type_map: TypeMap) -> GraphQLType:
    graphql_type: Optional[GraphQLType] = None

    # this adds support for type annotations that use
    # strings, without having to use get_type_hints

    if type(annotation) == str and annotation in type_map:
        return type_map[annotation].implementation  # type: ignore

    if is_scalar(annotation):
        graphql_type = get_scalar_type(annotation, type_map)

    elif hasattr(annotation, "_enum_definition"):
        graphql_type = get_enum_type(annotation._enum_definition, type_map)
    elif hasattr(annotation, "_type_definition"):
        from .object_type import get_object_type

        graphql_type = get_object_type(annotation, type_map)

    if not graphql_type:
        raise ValueError(f"Unable to get GraphQL type for {annotation}")

    return graphql_type


def get_graphql_type(
    field: Union[FieldDefinition, ArgumentDefinition],
    type_map: TypeMap,
) -> GraphQLType:
    # by default fields in GraphQL-Core are optional, but for us we only want
    # to mark optional fields when they are inside a Optional type hint
    wrap: Optional[Callable] = GraphQLNonNull

    type: GraphQLType
    field_type = cast(Type, field.type)

    if field.is_optional:
        wrap = None

    if field.is_list:
        child = cast(FieldDefinition, field.child)
        type = GraphQLList(get_graphql_type(child, type_map))

    elif field.is_union:
        union_definition = cast(StrawberryUnion, field_type)
        type = get_union_type(union_definition, type_map)
    else:
        type = get_type_for_annotation(field_type, type_map)

    if wrap:
        return wrap(type)

    return type

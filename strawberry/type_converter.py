import dataclasses
from collections.abc import AsyncGenerator

from graphql import GraphQLList, GraphQLNonNull

from .exceptions import MissingTypesForGenericError
from .type_registry import get_type_for_annotation
from .union import union
from .utils.str_converters import capitalize_first, to_camel_case
from .utils.typing import is_generic, is_union


def copy_annotation_with_types(annotation, *types):
    # unfortunately we need to have this back and forth with GraphQL types
    # and original classes for the time being. In future we might migrate
    # away from GraphQL-Core or build our own tiny class wrapper that will
    # help with generic types, but this works ok for now.
    origin = annotation.__origin__
    graphql_type = origin.graphql_type
    TypeClass = type(graphql_type)

    types_replacement_map = dict(
        zip([param.__name__ for param in origin.__parameters__], types)
    )
    copied_name = (
        "".join([capitalize_first(type.__name__) for type in types]) + graphql_type.name
    )

    extra_kwargs = {
        "description": graphql_type.description,
        "interfaces": graphql_type._interfaces,
    }

    def get_fields():
        origin_fields = dict(
            (to_camel_case(f.name), f) for f in dataclasses.fields(origin)
        )
        fields = graphql_type._fields(types_replacement_map)

        for field_name in fields.keys():
            origin_field = origin_fields[field_name]

            if is_generic(origin_field.type):
                fields[field_name] = copy_annotation_with_types(
                    origin_field.type, *types
                )

        return fields

    new_type = TypeClass(copied_name, get_fields, **extra_kwargs)

    # we use _copied to easily find a previously created type,
    # this is used by unions when needing to find the proper GraphQL
    # type when returning something
    # TODO: we could use this to prevent running all the code above

    if not hasattr(origin, "_copies"):
        origin._copies = {}

    origin._copies[types] = new_type

    return new_type


# TODO: make so that we don't pass force optional
# we use that when trying to get the type for a
# option field (which can either be a scalar or an object type)
def get_graphql_type_for_annotation(
    annotation, field_name: str, force_optional: bool = False
):
    # TODO: this might lead to issues with types that have a field value
    is_field_optional = force_optional

    if is_generic(annotation):
        types = getattr(annotation, "__args__", None)

        if types is None:
            raise MissingTypesForGenericError(field_name, annotation)

        graphql_type = copy_annotation_with_types(annotation, *types)
    elif hasattr(annotation, "graphql_type"):
        graphql_type = annotation.graphql_type
    else:
        annotation_name = getattr(annotation, "_name", None)

        if annotation_name == "List":
            list_of_type = get_graphql_type_for_annotation(
                annotation.__args__[0], field_name
            )

            list_type = GraphQLList(list_of_type)

            return list_type if is_field_optional else GraphQLNonNull(list_type)

        annotation_origin = getattr(annotation, "__origin__", None)

        if annotation_origin == AsyncGenerator:
            # async generators are used in subscription, we only need the yield type
            # https://docs.python.org/3/library/typing.html#typing.AsyncGenerator
            return get_graphql_type_for_annotation(annotation.__args__[0], field_name)

        elif is_union(annotation):
            types = annotation.__args__
            non_none_types = [x for x in types if x != None.__class__]  # noqa:E711

            # optionals are represented as Union[type, None]

            if len(non_none_types) == 1:
                is_field_optional = True
                graphql_type = get_graphql_type_for_annotation(
                    non_none_types[0], field_name, force_optional=True
                )
            else:
                is_field_optional = None.__class__ in types

                graphql_type = union(field_name, types).graphql_type
        else:
            graphql_type = get_type_for_annotation(annotation)

    if not graphql_type:
        raise ValueError(f"Unable to get GraphQL type for {annotation}")

    if is_field_optional:
        return graphql_type

    return GraphQLNonNull(graphql_type)

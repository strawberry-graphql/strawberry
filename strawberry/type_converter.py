from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLID,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLString,
    GraphQLUnionType,
)

from .scalars import ID


REGISTRY = {
    str: GraphQLString,
    int: GraphQLInt,
    float: GraphQLFloat,
    bool: GraphQLBoolean,
    ID: GraphQLID,
}


# TODO: make so that we don't pass force optional
# we use that when trying to get the type for a
# option field (which can either be a scalar or an object type)
def get_graphql_type_for_annotation(
    annotation, field_name: str, force_optional: bool = False
):
    # TODO: this might lead to issues with types that have a field value
    is_optional = force_optional

    if hasattr(annotation, "field"):
        graphql_type = annotation.field
    else:
        annotation_name = getattr(annotation, "_name", None)

        if annotation_name == "List":
            list_of_type = get_graphql_type_for_annotation(
                annotation.__args__[0], field_name
            )

            return GraphQLList(list_of_type)

        # for some reason _name is None for Optional and Union types, so we check if we
        # have __args__ populated, there might be some edge cases where __args__ is
        # populated but the type is not an Union, like in the above case with Lists
        if hasattr(annotation, "__args__"):
            types = annotation.__args__
            non_none_types = [x for x in types if x != None.__class__]  # noqa:E721

            # optionals are represented as Union[type, None]
            if len(non_none_types) == 1:
                is_optional = True
                graphql_type = get_graphql_type_for_annotation(
                    non_none_types[0], field_name, force_optional=True
                )
            else:
                is_optional = None.__class__ in types

                # TODO: union types don't work with scalar types
                # so we want to return a nice error
                # also we want to make sure we have been passed
                # strawberry types
                graphql_type = GraphQLUnionType(
                    field_name, [type.field for type in types]
                )
        else:
            graphql_type = REGISTRY.get(annotation)

    if not graphql_type:
        raise ValueError(f"Unable to get GraphQL type for {annotation}")

    if is_optional:
        return graphql_type

    return GraphQLNonNull(graphql_type)

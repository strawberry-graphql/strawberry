from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLInt,
    GraphQLNonNull,
    GraphQLString,
    GraphQLUnionType,
)

TYPE_MAP = {
    str: GraphQLString,
    int: GraphQLInt,
    float: GraphQLFloat,
    bool: GraphQLBoolean,
}


# TODO: make so that we don't pass force optional
# we use that when trying to get the type for a
# option field (which can either be a scalar or an object type)
def get_graphql_type_for_annotation(
    annotation, field_name: str, force_optional: bool = False
):
    # TODO: nice error

    # TODO: this might lead to issues with types that have a
    # field value
    if hasattr(annotation, "field"):
        return annotation.field

    is_optional = False

    # checking for optional and union types
    if hasattr(annotation, "__args__"):
        types = annotation.__args__
        non_none_types = [x for x in types if x != type(None)]

        # optionals are represented as Union[type, None]
        if len(non_none_types) == 1:
            is_optional = True
            graphql_type = get_graphql_type_for_annotation(
                non_none_types[0], field_name, force_optional=True
            )
        else:
            is_optional = type(None) in types

            # TODO: union types don't work with scalar types
            # so we want to return a nice error
            # also we want to make sure we have been passed
            # strawberry types
            graphql_type = GraphQLUnionType(field_name, [type.field for type in types])
    else:
        graphql_type = TYPE_MAP.get(annotation)

    if not graphql_type:
        raise ValueError(f"Unable to get GraphQL type for {annotation}")

    if is_optional or force_optional:
        return graphql_type

    return GraphQLNonNull(graphql_type)

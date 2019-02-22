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


def get_graphql_type_for_annotation(annotation, field_name: str):
    # TODO: nice error

    is_optional = False

    # checking for optional and union types
    if hasattr(annotation, "__args__"):
        # TODO: might not be true
        is_optional = True

        types = annotation.__args__
        non_none_types = [x for x in types if x != type(None)]

        if len(non_none_types) == 1:
            graphql_type = TYPE_MAP.get(non_none_types[0])
        else:
            graphql_type = GraphQLUnionType(field_name, [GraphQLInt, GraphQLString])
    else:
        graphql_type = TYPE_MAP.get(annotation)

    if not graphql_type:
        raise ValueError(f"Unable to get GraphQL type for {annotation}")

    if is_optional:
        return graphql_type

    return GraphQLNonNull(graphql_type)

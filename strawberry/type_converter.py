from functools import singledispatch

from graphql import GraphQLString

TYPE_MAP = {str: GraphQLString}


@singledispatch
def get_graphql_type_for_annotation(annotation):
    # TODO: nice error
    # TODO: handle special cases (unions, optional)
    return TYPE_MAP.get(annotation)

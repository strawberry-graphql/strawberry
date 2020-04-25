from graphql.utilities.print_schema import print_type as graphql_print


def print_type(type_) -> str:
    """Returns a string representation of a strawberry type"""

    return graphql_print(type_.graphql_type)

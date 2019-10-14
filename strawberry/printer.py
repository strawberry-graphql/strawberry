from graphql.utilities.schema_printer import print_type as graphql_print


def print_type(type_) -> str:
    """Returns a string representation of a strawberry type"""

    return graphql_print(type_.field)

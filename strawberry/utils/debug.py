import datetime
import json
import typing

from pygments import highlight, lexers
from pygments.formatters import Terminal256Formatter

from .graphql_lexer import GraphQLLexer


def pretty_print_graphql_operation(
    operation_name: str, query: str, variables: typing.Dict["str", typing.Any]
):  # pragma: no cover
    """Pretty print a GraphQL operation using pygments.

    Won't print introspection operation to prevent noise in the output."""

    if operation_name == "IntrospectionQuery":
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[{now}]: {operation_name or 'No operation name'}")
    print(highlight(query, GraphQLLexer(), Terminal256Formatter()))

    if variables:
        variables_json = json.dumps(variables, indent=4)

        print(highlight(variables_json, lexers.JsonLexer(), Terminal256Formatter()))

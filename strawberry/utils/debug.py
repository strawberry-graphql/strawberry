import datetime
import json
from json import JSONEncoder
from typing import Any, Dict, Optional

from pygments import highlight, lexers
from pygments.formatters import Terminal256Formatter

from .graphql_lexer import GraphQLLexer


class StrawberryJSONEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        return repr(o)


def pretty_print_graphql_operation(
    operation_name: Optional[str], query: str, variables: Optional[Dict["str", Any]]
):
    """Pretty print a GraphQL operation using pygments.

    Won't print introspection operation to prevent noise in the output."""

    if operation_name == "IntrospectionQuery":
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[{now}]: {operation_name or 'No operation name'}")
    print(highlight(query, GraphQLLexer(), Terminal256Formatter()))

    if variables:
        variables_json = json.dumps(variables, indent=4, cls=StrawberryJSONEncoder)

        print(highlight(variables_json, lexers.JsonLexer(), Terminal256Formatter()))

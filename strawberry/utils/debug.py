import datetime
import json
from json import JSONEncoder
from typing import Any, Dict, Optional


class StrawberryJSONEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        return repr(o)


def pretty_print_graphql_operation(
    operation_name: Optional[str], query: str, variables: Optional[Dict["str", Any]]
) -> None:
    """Pretty print a GraphQL operation using pygments.

    Won't print introspection operation to prevent noise in the output.
    """
    try:
        from pygments import highlight, lexers
        from pygments.formatters import Terminal256Formatter
    except ImportError as e:
        raise ImportError(
            "pygments is not installed but is required for debug output, install it "
            "directly or run `pip install strawberry-graphql[debug-server]`"
        ) from e

    from .graphql_lexer import GraphQLLexer

    if operation_name == "IntrospectionQuery":
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[{now}]: {operation_name or 'No operation name'}")  # noqa: T201
    print(highlight(query, GraphQLLexer(), Terminal256Formatter()))  # noqa: T201

    if variables:
        variables_json = json.dumps(variables, indent=4, cls=StrawberryJSONEncoder)

        print(  # noqa: T201
            highlight(variables_json, lexers.JsonLexer(), Terminal256Formatter())
        )


__all__ = ["pretty_print_graphql_operation"]

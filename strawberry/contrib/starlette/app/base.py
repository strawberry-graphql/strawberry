import datetime
import json
import typing

from pygments import highlight, lexers
from pygments.formatters import Terminal256Formatter

from ..utils.graphql_lexer import GraphqlLexer


class BaseApp:
    def __init__(self, schema) -> None:
        self.schema = schema

    def _debug_log(
        self, operation_name: str, query: str, variables: typing.Dict["str", typing.Any]
    ):
        if operation_name == "IntrospectionQuery":
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{now}]: {operation_name or 'No operation name'}")
        print(highlight(query, GraphqlLexer(), Terminal256Formatter()))

        if variables:
            variables_json = json.dumps(variables, indent=4)

            print(highlight(variables_json, lexers.JsonLexer(), Terminal256Formatter()))

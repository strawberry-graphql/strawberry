import datetime
import json
import sys
from contextlib import redirect_stdout
from json import JSONEncoder
from typing import Any, Dict, List, Optional, TextIO

from pygments import highlight, lexers
from pygments.formatters import Terminal256Formatter

from graphql.error.graphql_error import GraphQLError

from strawberry.http import process_result
from strawberry.types.execution import ExecutionContext, ExecutionResult

from .graphql_lexer import GraphQLLexer


class StrawberryJSONEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        return repr(o)


def pretty_print_graphql_operation(
    operation_name: Optional[str],
    query: str,
    variables: Optional[Dict["str", Any]],
):
    """
    Deprecated
    Please use `strawberry.utils.debug.pretty_print_graphql_execution_context` instead!
    ---
    Pretty print a GraphQL operation using pygments.
    Won't print introspection operation to prevent noise in the output.
    """
    if "query IntrospectionQuery" in query:
        return

    pretty_print_graphql_execution_context(
        operation_name, query, variables, attach_timestamp=True
    )


def pretty_print_graphql_execution_context(
    operation_name: Optional[str],
    query: str,
    variables: Optional[Dict["str", Any]],
    attach_timestamp=False,
    stream: TextIO = None,
):
    if stream is None:
        stream = sys.stdout

    with redirect_stdout(stream):

        operation_name = operation_name or "No operation name"

        if attach_timestamp:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}]: {operation_name}")
        else:
            print(operation_name)

        print(highlight(query, GraphQLLexer(), Terminal256Formatter()))

        if variables:
            variables_json = json.dumps(variables, indent=4, cls=StrawberryJSONEncoder)
            print(highlight(variables_json, lexers.JsonLexer(), Terminal256Formatter()))


def pretty_print_graphql_execution_result(
    data: Optional[Dict[str, Any]],
    errors: Optional[List[GraphQLError]],
    extensions: Optional[Dict[str, Any]] = None,
    stream: TextIO = None,
):
    if stream is None:
        stream = sys.stdout

    formatted_json = json.dumps(
        process_result(ExecutionResult(data, errors, extensions)),
        indent=4,
        cls=StrawberryJSONEncoder,
    )

    colorful_json = highlight(
        formatted_json, lexers.JsonLexer(), Terminal256Formatter()
    )

    with redirect_stdout(stream):
        print(colorful_json.rstrip("\n"))


def pretty_print_graphql(
    execution_context: ExecutionContext,
    execution_result: ExecutionResult,
    skip_introspection_queries=False,
    stream: TextIO = None,
):
    if stream is None:
        stream = sys.stdout

    if (
        "query IntrospectionQuery" in execution_context.query
        and skip_introspection_queries
    ):
        #  IntrospectionQuery is not always set as operation_name
        #  ( single query, operation_name can be ommited )
        #  So we have too look for it in the query.
        return

    pretty_print_graphql_execution_context(
        execution_context.operation_name,
        execution_context.query,
        execution_context.variables,
        stream=stream,
    )

    pretty_print_graphql_execution_result(
        execution_result.data,
        execution_result.errors,
        execution_result.extensions,
        stream=stream,
    )

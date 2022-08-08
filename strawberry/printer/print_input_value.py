from __future__ import annotations

from graphql import GraphQLArgument
from graphql.language.printer import print_ast
from graphql.utilities.print_schema import print_deprecated

from .ast_from_value import ast_from_value


def print_input_value(name: str, arg: GraphQLArgument) -> str:
    default_ast = ast_from_value(arg.default_value, arg.type)
    arg_decl = f"{name}: {arg.type}"
    if default_ast:
        arg_decl += f" = {print_ast(default_ast)}"
    return arg_decl + print_deprecated(arg.deprecation_reason)

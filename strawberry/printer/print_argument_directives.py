from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import GraphQLArgument

from .print_extras import PrintExtras
from .print_schema_directives import print_schema_directive


if TYPE_CHECKING:
    from strawberry.schema import BaseSchema


def print_argument_directives(
    argument: GraphQLArgument, *, schema: BaseSchema, extras: PrintExtras
) -> str:
    strawberry_type = argument.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    return "".join(
        (
            print_schema_directive(directive, schema=schema, extras=extras)
            for directive in directives
        )
    )

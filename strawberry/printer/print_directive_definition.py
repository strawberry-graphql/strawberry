from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from graphql.type import GraphQLDirective
from graphql.utilities.print_schema import print_description

from strawberry.schema_directive import StrawberrySchemaDirective

from .print_extras import PrintExtras


if TYPE_CHECKING:
    from strawberry.schema import BaseSchema


def should_print_directive_definition(directive: GraphQLDirective) -> bool:
    strawberry_directive = directive.extensions["strawberry-definition"]

    return (
        not isinstance(strawberry_directive, StrawberrySchemaDirective)
        or strawberry_directive.print_definition
    )


def print_directive_definition(
    directive: GraphQLDirective, *, schema: BaseSchema
) -> Optional[str]:
    from .print_args import print_args

    if should_print_directive_definition(directive):
        return (
            print_description(directive)
            + f"directive @{directive.name}"
            # TODO: add support for directives on arguments directives
            + print_args(directive.args, schema=schema, extras=PrintExtras())
            + (" repeatable" if directive.is_repeatable else "")
            + " on "
            + " | ".join(location.name for location in directive.locations)
        )

    return None

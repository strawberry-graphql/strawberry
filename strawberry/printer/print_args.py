from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from graphql.type import GraphQLArgument
from graphql.utilities.print_schema import print_description

from .print_extras import PrintExtras
from .print_input_value import print_input_value


if TYPE_CHECKING:
    from strawberry.schema import BaseSchema


def print_args(
    args: Dict[str, GraphQLArgument],
    indentation: str = "",
    *,
    schema: BaseSchema,
    extras: PrintExtras,
) -> str:
    from .print_argument_directives import print_argument_directives

    if not args:
        return ""

    # If every arg does not have a description, print them on one line.
    if not any(arg.description for arg in args.values()):
        return (
            "("
            + ", ".join(
                (
                    f"{print_input_value(name, arg)}"
                    f"{print_argument_directives(arg, schema=schema, extras=extras)}"
                )
                for name, arg in args.items()
            )
            + ")"
        )

    return (
        "(\n"
        + "\n".join(
            print_description(arg, f"  {indentation}", not i)
            + f"  {indentation}"
            + print_input_value(name, arg)
            + print_argument_directives(arg, schema=schema, extras=extras)
            for i, (name, arg) in enumerate(args.items())
        )
        + f"\n{indentation})"
    )

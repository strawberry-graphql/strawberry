from __future__ import annotations

from typing import Sequence

import libcst as cst
import libcst.matchers as m
from libcst._nodes.expression import BaseExpression, Call  # noqa: TCH002
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor


def _find_named_argument(args: Sequence[cst.Arg], name: str) -> cst.Arg | None:
    return next(
        (arg for arg in args if arg.keyword and arg.keyword.value == name),
        None,
    )


def _find_positional_argument(
    args: Sequence[cst.Arg], search_index: int
) -> cst.Arg | None:
    for index, arg in enumerate(args):
        if index > search_index:
            return None

        if index == search_index and arg.keyword is None:
            return arg


class ConvertUnionToAnnotatedUnion(VisitorBasedCodemodCommand):
    # TODO: support Union and | syntax, also in errors? ugh
    DESCRIPTION: str = (
        "Converts strawberry.union(..., types=(...)) to "
        "Annotated[Union[...], strawberry.union(...)]"
    )

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)

    @m.leave(
        m.Call(
            func=m.Attribute(value=m.Name("strawberry"), attr=m.Name("union"))
            | m.Name("union")
        )
    )
    def leave_union_call(
        self, original_node: Call, updated_node: Call
    ) -> BaseExpression:
        types = _find_named_argument(original_node.args, "types")
        union_name = _find_named_argument(original_node.args, "name")

        if types is None:
            types = _find_positional_argument(original_node.args, 1)

        # this is probably a strawberry.union(name="...") so we skip the conversion
        # as it is going to be used in the new way already 😊

        if types is None:
            return original_node

        AddImportsVisitor.add_needed_import(
            self.context, "typing_extensions", "Annotated"
        )

        RemoveImportsVisitor.remove_unused_import(self.context, "strawberry", "union")

        if union_name is None:
            union_name = _find_positional_argument(original_node.args, 0)

        assert union_name
        assert isinstance(types.value, (cst.Tuple, cst.List))

        types = types.value.elements
        union_name = union_name.value

        description = _find_named_argument(original_node.args, "description")
        directives = _find_named_argument(original_node.args, "directives")

        union_node = cst.Subscript(
            value=cst.Name(value="Union"),
            slice=[cst.SubscriptElement(slice=cst.Index(value=t.value)) for t in types],
        )

        union_call_args = [
            cst.Arg(
                value=union_name,
                keyword=cst.Name(value="name"),
                equal=cst.AssignEqual(
                    whitespace_before=cst.SimpleWhitespace(""),
                    whitespace_after=cst.SimpleWhitespace(""),
                ),
            )
        ]

        additional_args = {"description": description, "directives": directives}

        union_call_args.extend(
            cst.Arg(
                value=arg.value,
                keyword=cst.Name(name),
                equal=cst.AssignEqual(
                    whitespace_before=cst.SimpleWhitespace(""),
                    whitespace_after=cst.SimpleWhitespace(""),
                ),
            )
            for name, arg in additional_args.items()
            if arg is not None
        )

        union_call_node = cst.Call(
            func=cst.Attribute(
                value=cst.Name(value="strawberry"),
                attr=cst.Name(value="union"),
            ),
            args=union_call_args,
        )

        return cst.Subscript(
            value=cst.Name(value="Annotated"),
            slice=[
                cst.SubscriptElement(
                    slice=cst.Index(
                        value=union_node,
                    ),
                ),
                cst.SubscriptElement(
                    slice=cst.Index(
                        value=union_call_node,
                    ),
                ),
            ],
        )

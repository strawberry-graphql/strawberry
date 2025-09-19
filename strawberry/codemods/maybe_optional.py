from __future__ import annotations

import libcst as cst
import libcst.matchers as m
from libcst._nodes.expression import BaseExpression  # noqa: TC002
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


class ConvertMaybeToOptional(VisitorBasedCodemodCommand):
    DESCRIPTION: str = (
        "Converts strawberry.Maybe[T] to strawberry.Maybe[T | None] "
        "to match the new Maybe type definition"
    )

    def __init__(
        self,
        context: CodemodContext,
        use_pipe_syntax: bool = True,  # Default to pipe syntax for modern Python
    ) -> None:
        self.use_pipe_syntax = use_pipe_syntax
        super().__init__(context)

    @m.leave(
        m.Subscript(
            value=m.Attribute(value=m.Name("strawberry"), attr=m.Name("Maybe"))
            | m.Name("Maybe")
        )
    )
    def leave_maybe_subscript(
        self, original_node: cst.Subscript, updated_node: cst.Subscript
    ) -> BaseExpression:
        # Skip if it's not a strawberry.Maybe or imported Maybe
        if isinstance(original_node.value, cst.Name):
            # Check if this is an imported Maybe from strawberry
            # For now, we'll assume any standalone "Maybe" is from strawberry
            # In a more robust implementation, we'd track imports
            pass

        # Get the inner type
        if isinstance(original_node.slice, (list, tuple)):
            if len(original_node.slice) != 1:
                return original_node
            slice_element = original_node.slice[0]
        else:
            slice_element = original_node.slice

        if not isinstance(slice_element, cst.SubscriptElement):
            return original_node

        if not isinstance(slice_element.slice, cst.Index):
            return original_node

        inner_type = slice_element.slice.value

        # Check if the inner type already includes None
        if self._already_includes_none(inner_type):
            return original_node

        # Create the new union type with None
        new_type: BaseExpression
        if self.use_pipe_syntax:
            new_type = cst.BinaryOperation(
                left=inner_type,
                operator=cst.BitOr(
                    whitespace_before=cst.SimpleWhitespace(" "),
                    whitespace_after=cst.SimpleWhitespace(" "),
                ),
                right=cst.Name("None"),
            )
        else:
            # Use Union[T, None] syntax
            AddImportsVisitor.add_needed_import(self.context, "typing", "Union")
            new_type = cst.Subscript(
                value=cst.Name("Union"),
                slice=[
                    cst.SubscriptElement(slice=cst.Index(value=inner_type)),
                    cst.SubscriptElement(slice=cst.Index(value=cst.Name("None"))),
                ],
            )

        # Return the updated Maybe[T | None]
        return updated_node.with_changes(
            slice=[cst.SubscriptElement(slice=cst.Index(value=new_type))]
        )

    def _already_includes_none(self, node: BaseExpression) -> bool:
        """Check if the type already includes None (e.g., T | None or Union[T, None])."""
        # Check for T | None pattern
        if isinstance(node, cst.BinaryOperation) and isinstance(
            node.operator, cst.BitOr
        ):
            if isinstance(node.right, cst.Name) and node.right.value == "None":
                return True
            # Recursively check left side for chained unions
            if self._already_includes_none(node.left):
                return True

        # Check for Union[..., None] pattern
        if (
            isinstance(node, cst.Subscript)
            and isinstance(node.value, cst.Name)
            and node.value.value == "Union"
        ):
            # Handle both list and tuple slice formats
            slice_elements = (
                node.slice if isinstance(node.slice, (list, tuple)) else [node.slice]
            )
            for element in slice_elements:
                if (
                    isinstance(element, cst.SubscriptElement)
                    and isinstance(element.slice, cst.Index)
                    and isinstance(element.slice.value, cst.Name)
                    and element.slice.value.value == "None"
                ):
                    return True

        return False

from __future__ import annotations

import libcst as cst
import libcst.matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor


class UpdateImportsCodemod(VisitorBasedCodemodCommand):
    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self.add_imports_visitor = AddImportsVisitor(context)
        self.remove_imports_visitor = RemoveImportsVisitor(context)

    # >>> from strawberry.field import something
    def leave_ImportFrom(
        self, node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        if m.matches(
            node,
            m.ImportFrom(
                module=m.Attribute(value=m.Name("strawberry"), attr=m.Name("field"))
            ),
        ):
            updated_node = updated_node.with_changes(
                module=cst.Attribute(
                    value=cst.Attribute(
                        value=cst.Name("strawberry"), attr=cst.Name("types")
                    ),
                    attr=cst.Name("field"),
                ),
            )

        return updated_node

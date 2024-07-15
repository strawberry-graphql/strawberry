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

    def _update_strawberry_field_imports(
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

    def _update_strawberry_type_imports(
        self, node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        if m.matches(
            node,
            m.ImportFrom(
                module=m.Attribute(value=m.Name("strawberry"), attr=m.Name("type"))
            ),
        ):
            has_get_object_definition = any(
                m.matches(name, m.ImportAlias(name=m.Name("get_object_definition")))
                for name in node.names
            )

            updated_node = updated_node.with_changes(
                module=cst.Attribute(
                    value=cst.Attribute(
                        value=cst.Name("strawberry"), attr=cst.Name("types")
                    ),
                    attr=cst.Name("base"),
                ),
            )

            self.remove_imports_visitor.remove_unused_import(
                self.context, "strawberry.types.base", "get_object_definition"
            )

            if has_get_object_definition:
                self.add_imports_visitor.add_needed_import(
                    self.context, "strawberry.types", "get_object_definition"
                )

        return updated_node

    def leave_ImportFrom(
        self, node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        updated_node = self._update_strawberry_field_imports(updated_node, updated_node)
        updated_node = self._update_strawberry_type_imports(updated_node, updated_node)

        return updated_node

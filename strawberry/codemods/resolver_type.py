from __future__ import annotations

from typing import List, Optional, Union

import libcst as cst
import libcst.matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


def _get_field_specifier_name_matcher() -> m.OneOf[m.Name]:
    return m.OneOf(
        m.Name("field"),
        m.Name("mutation"),
        m.Name("subscription"),
    )


class ConvertFieldWithResolverTypeAnnotations(VisitorBasedCodemodCommand):
    DESCRIPTION: str = (
        "Converts field: T = strawberry.field(resolver=...) to "
        "field: strawberry.Resolver[T] = strawberry.field(resolver=...)"
        " or similar for mutation and subscription"
    )

    def __init__(
        self,
        context: CodemodContext,
    ) -> None:
        self._is_using_named_import = False

        super().__init__(context)

    def visit_Module(self, node: cst.Module) -> Optional[bool]:
        self._is_using_named_import = False

        return super().visit_Module(node)

    @m.visit(
        m.ImportFrom(
            m.Name("strawberry"),
            [
                m.ZeroOrMore(),
                m.ImportAlias(_get_field_specifier_name_matcher()),
                m.ZeroOrMore(),
            ],
        )
    )
    def visit_import_from(self, original_node: cst.ImportFrom) -> None:
        self._is_using_named_import = True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        new_body = []

        for node in updated_node.body.body:
            if not m.matches(
                node,
                m.SimpleStatementLine(
                    body=[
                        m.AnnAssign(value=self._field_with_resolver_call_matcher()),
                    ]
                ),
            ):
                new_body.append(node)
                continue

            self._add_imports()

            node_stmt = cst.ensure_type(node, cst.SimpleStatementLine)
            ann_assign = cst.ensure_type(node_stmt.body[0], cst.AnnAssign)

            new_annotation = self._new_annotation_wrapped_in_resolver(
                ann_assign.annotation
            )

            new_body.append(
                node_stmt.with_changes(
                    body=[
                        ann_assign.with_changes(
                            annotation=new_annotation,
                        )
                    ]
                )
            )

        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=new_body)
        )

    def _field_with_resolver_call_matcher(self) -> m.Call:
        """Matches a call to strawberry.field with a resolver argument."""

        args: List[Union[m.ArgMatchType, m.AtLeastN[m.DoNotCareSentinel]]] = [
            m.ZeroOrMore(),
            m.Arg(
                keyword=m.Name("resolver"),
            ),
            m.ZeroOrMore(),
        ]

        if self._is_using_named_import:
            return m.Call(
                func=_get_field_specifier_name_matcher(),
                args=args,
            )

        return m.Call(
            func=m.Attribute(
                value=m.Name("strawberry"),
                attr=_get_field_specifier_name_matcher(),
            ),
            args=args,
        )

    def _add_imports(self) -> None:
        """Add named import of Resolver if this module uses named import of field."""
        if self._is_using_named_import:
            AddImportsVisitor.add_needed_import(
                self.context,
                "strawberry",
                "Resolver",
            )

    def _new_annotation_wrapped_in_resolver(
        self, annotation: cst.Annotation
    ) -> cst.Annotation:
        """Wraps the annotation in a strawberry.Resolver[] type."""

        if self._is_using_named_import:
            resolver_type: Union[cst.Name, cst.Attribute] = cst.Name("Resolver")
        else:
            resolver_type = cst.Attribute(
                value=cst.Name("strawberry"),
                attr=cst.Name("Resolver"),
            )

        return annotation.with_changes(
            annotation=cst.Subscript(
                value=resolver_type,
                slice=[
                    cst.SubscriptElement(
                        slice=cst.Index(value=annotation.annotation),
                    ),
                ],
            )
        )

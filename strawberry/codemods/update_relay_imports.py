from __future__ import annotations

import libcst as cst
import libcst.matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor

PAGINATION_SYMBOLS = {
    "Connection",
    "ConnectionExtension",
    "Edge",
    "ListConnection",
    "NodeType",
    "PageInfo",
    "connection",
    "from_base64",
    "to_base64",
}

MODULE_MAPPING = {
    "strawberry.relay.types": "strawberry.pagination.types",
    "strawberry.relay.fields": "strawberry.pagination.fields",
    "strawberry.relay.utils": "strawberry.pagination.utils",
}


def _build_module_node(dotted_name: str) -> cst.BaseExpression:
    parts = dotted_name.split(".")
    result: cst.BaseExpression = cst.Name(parts[0])
    for part in parts[1:]:
        result = cst.Attribute(value=result, attr=cst.Name(part))
    return result


class UpdateRelayImportsCodemod(VisitorBasedCodemodCommand):
    DESCRIPTION = (
        "Migrates pagination imports from strawberry.relay to strawberry.pagination "
        "and renames relay_max_results to connection_max_results."
    )

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self.add_imports_visitor = AddImportsVisitor(context)
        self.remove_imports_visitor = RemoveImportsVisitor(context)

    def _get_dotted_name(self, node: cst.BaseExpression) -> str | None:
        if isinstance(node, cst.Name):
            return node.value
        if isinstance(node, cst.Attribute):
            parent = self._get_dotted_name(node.value)
            if parent:
                return f"{parent}.{node.attr.value}"
        return None

    def leave_ImportFrom(  # noqa: N802
        self, node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom | cst.RemovalSentinel:
        if updated_node.module is None:
            return updated_node

        module_name = self._get_dotted_name(updated_node.module)
        if module_name is None:
            return updated_node

        if module_name in MODULE_MAPPING:
            new_module = MODULE_MAPPING[module_name]
            return updated_node.with_changes(module=_build_module_node(new_module))

        if module_name == "strawberry.relay":
            return self._split_relay_imports(updated_node)

        return updated_node

    def _split_relay_imports(
        self, updated: cst.ImportFrom
    ) -> cst.ImportFrom | cst.RemovalSentinel:
        if isinstance(updated.names, cst.ImportStar):
            return updated

        pagination_aliases: list[cst.ImportAlias] = []
        relay_aliases: list[cst.ImportAlias] = []

        for alias in updated.names:
            if (
                isinstance(alias.name, cst.Name)
                and alias.name.value in PAGINATION_SYMBOLS
            ):
                pagination_aliases.append(alias)
            else:
                relay_aliases.append(alias)

        if not pagination_aliases:
            return updated

        if not relay_aliases:
            return updated.with_changes(
                module=_build_module_node("strawberry.pagination")
            )

        # Mixed: use add/remove for simple imports, preserving aliases
        for alias in pagination_aliases:
            assert isinstance(alias.name, cst.Name)
            name = alias.name.value
            asname = (
                alias.asname.name.value
                if alias.asname and isinstance(alias.asname.name, cst.Name)
                else None
            )
            self.add_imports_visitor.add_needed_import(
                self.context, "strawberry.pagination", name, asname
            )
            self.remove_imports_visitor.remove_unused_import(
                self.context, "strawberry.relay", name, asname
            )

        return updated.with_changes(names=relay_aliases)

    def leave_Call(  # noqa: N802
        self, node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        if not m.matches(
            updated_node, m.Call(func=m.Name("StrawberryConfig"))
        ) and not m.matches(
            updated_node,
            m.Call(func=m.Attribute(attr=m.Name("StrawberryConfig"))),
        ):
            return updated_node

        new_args = []
        changed = False
        for arg in updated_node.args:
            if m.matches(arg, m.Arg(keyword=m.Name("relay_max_results"))):
                new_args.append(
                    arg.with_changes(keyword=cst.Name("connection_max_results"))
                )
                changed = True
            else:
                new_args.append(arg)

        if changed:
            return updated_node.with_changes(args=new_args)
        return updated_node

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.helpers import get_full_name_for_node

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence


_OPENTELEMETRY_EXTENSIONS = frozenset(
    {"OpenTelemetryExtension", "OpenTelemetryExtensionSync"}
)
_APOLLO_EXTENSIONS = frozenset({"ApolloTracingExtension", "ApolloTracingExtensionSync"})
_APOLLO_FEDERATION_EXTENSIONS = frozenset(
    {"ApolloFederationTracingExtension", "ApolloFederationTracingExtensionSync"}
)
_DATADOG_EXTENSIONS = frozenset(
    {"DatadogTracingExtension", "DatadogTracingExtensionSync"}
)
# Classes whose hooks receive strawberry.Info, by the modules that export them.
_EXTENSION_BASES: dict[str, frozenset[str]] = {
    "strawberry.extensions": frozenset({"SchemaExtension"}),
    "strawberry.extensions.base_extension": frozenset({"SchemaExtension"}),
    "strawberry.extensions.directives": frozenset(
        {"DirectivesExtension", "DirectivesExtensionSync"}
    ),
    "strawberry.extensions.tracing": _OPENTELEMETRY_EXTENSIONS
    | _APOLLO_EXTENSIONS
    | _APOLLO_FEDERATION_EXTENSIONS
    | _DATADOG_EXTENSIONS,
    "strawberry.extensions.tracing.apollo": _APOLLO_EXTENSIONS,
    "strawberry.extensions.tracing.apollo_federation": _APOLLO_FEDERATION_EXTENSIONS,
    "strawberry.extensions.tracing.datadog": _DATADOG_EXTENSIONS,
    "strawberry.extensions.tracing.opentelemetry": _OPENTELEMETRY_EXTENSIONS,
}
# Hooks that receive Info, with the position of `info` when it has another name.
_RESOLVE_HOOK = {"resolve": 3}
_OPENTELEMETRY_HOOKS = {"add_tags": 2, "filter_resolver_args": 2}


def _imported_name(alias: cst.ImportAlias) -> str | None:
    if alias.asname and isinstance(alias.asname.name, cst.Name):
        return alias.asname.name.value
    if isinstance(alias.name, cst.Name):
        return alias.name.value
    return None


class _NameCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Name(self, node: cst.Name) -> None:  # noqa: N802
        self.names.add(node.value)


class _SuperCallInfoRewriter(cst.CSTTransformer):
    """Passes Strawberry's Info to ``super()`` calls of the converted hooks."""

    def __init__(
        self, hooks: Collection[str], original_name: str, strawberry_name: str
    ) -> None:
        super().__init__()
        self._hooks = hooks
        self._original_name = original_name
        self._strawberry_name = strawberry_name

    # super() means something else inside nested scopes
    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:  # noqa: N802
        return False

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:  # noqa: N802
        return False

    def visit_Lambda(self, node: cst.Lambda) -> bool:  # noqa: N802
        return False

    def leave_Call(  # noqa: N802
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        func = updated_node.func
        if not (
            isinstance(func, cst.Attribute)
            and func.attr.value in self._hooks
            and isinstance(func.value, cst.Call)
            and isinstance(func.value.func, cst.Name)
            and func.value.func.value == "super"
        ):
            return updated_node

        return updated_node.with_changes(
            args=[
                arg.with_changes(value=cst.Name(self._strawberry_name))
                if isinstance(arg.value, cst.Name)
                and arg.value.value == self._original_name
                else arg
                for arg in updated_node.args
            ]
        )


class ConvertSchemaExtensionInfo(VisitorBasedCodemodCommand):
    DESCRIPTION = (
        "Opts schema extension hooks into strawberry.Info while preserving their "
        "existing graphql-core Info behavior."
    )

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        # Local names of extension base classes, mapped to their original names.
        self._extension_base_names: dict[str, str] = {}
        self._strawberry_info_names: set[str] = set()
        self._graphql_info_names: set[str] = {"GraphQLResolveInfo"}
        self._graphql_info_imports: dict[str, tuple[str, str | None]] = {}
        self._strawberry_module_names: set[str] = {"strawberry"}
        # The hooks to convert for each class being visited.
        self._class_stack: list[dict[str, int]] = []
        self._class_function_depths: list[int] = []
        self._function_depth = 0

    def visit_Import(self, node: cst.Import) -> None:  # noqa: N802
        for alias in node.names:
            imported_module = get_full_name_for_node(alias.name)
            if imported_module == "strawberry":
                self._strawberry_module_names.add(_imported_name(alias) or "strawberry")
            elif imported_module in _EXTENSION_BASES and alias.asname:
                imported_name = _imported_name(alias)
                if imported_name:
                    for class_name in _EXTENSION_BASES[imported_module]:
                        self._extension_base_names[f"{imported_name}.{class_name}"] = (
                            class_name
                        )

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:  # noqa: N802
        module_name = get_full_name_for_node(node.module) if node.module else None
        if isinstance(node.names, cst.ImportStar):
            return

        for alias in node.names:
            original_name = get_full_name_for_node(alias.name)
            imported_name = _imported_name(alias)
            if original_name is None or imported_name is None:
                continue

            if original_name in _EXTENSION_BASES.get(module_name or "", ()):
                self._extension_base_names[imported_name] = original_name
            elif (
                module_name
                in {"strawberry", "strawberry.types", "strawberry.types.info"}
                and original_name == "Info"
            ):
                self._strawberry_info_names.add(imported_name)
            elif (
                module_name in {"graphql", "graphql.type"}
                and original_name == "GraphQLResolveInfo"
            ):
                self._graphql_info_names.add(imported_name)
                self._graphql_info_imports[imported_name] = (
                    module_name,
                    imported_name if imported_name != original_name else None,
                )

    def visit_ClassDef(self, node: cst.ClassDef) -> None:  # noqa: N802
        base_names = {
            base_name
            for base in node.bases
            if (base_name := self._extension_base_name(base.value)) is not None
        }
        hooks: dict[str, int] = {}
        if base_names:
            hooks.update(_RESOLVE_HOOK)
        if base_names & _OPENTELEMETRY_EXTENSIONS:
            hooks.update(_OPENTELEMETRY_HOOKS)
        self._class_stack.append(hooks)
        self._class_function_depths.append(self._function_depth)

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        self._class_stack.pop()
        self._class_function_depths.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:  # noqa: N802
        self._function_depth += 1

    def leave_FunctionDef(  # noqa: N802
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        is_direct_class_method = (
            bool(self._class_function_depths)
            and self._function_depth == self._class_function_depths[-1] + 1
        )
        self._function_depth -= 1
        hooks = self._class_stack[-1] if self._class_stack else {}
        method_name = original_node.name.value
        if not is_direct_class_method or method_name not in hooks:
            return updated_node

        parameter = self._find_info_parameter(updated_node.params, hooks[method_name])
        if parameter is None:
            self.warn(
                f"Skipped {method_name} because its info parameter "
                "could not be identified."
            )
            return updated_node

        annotation_kind = self._annotation_kind(parameter.annotation)
        if annotation_kind == "strawberry":
            return updated_node
        if annotation_kind == "unknown":
            self.warn(
                f"Skipped {original_node.name.value}: the annotation on "
                f"`{parameter.name.value}` is not a recognized graphql-core Info type."
            )
            return updated_node

        collector = _NameCollector()
        updated_node.visit(collector)
        strawberry_info_name = "strawberry_info"
        while strawberry_info_name in collector.names:
            strawberry_info_name = f"_{strawberry_info_name}"

        original_info_name = parameter.name.value
        updated_parameter = parameter.with_changes(
            name=cst.Name(strawberry_info_name),
            annotation=cst.Annotation(
                cst.Attribute(
                    value=cst.Name("strawberry"),
                    attr=cst.Name("Info"),
                )
            ),
        )
        updated_params = self._replace_parameter(
            updated_node.params, parameter, updated_parameter
        )
        updated_body = updated_node.body.visit(
            _SuperCallInfoRewriter(hooks, original_info_name, strawberry_info_name)
        )
        assert isinstance(updated_body, cst.BaseSuite)
        updated_body = self._add_raw_info_alias(
            updated_body,
            original_info_name=original_info_name,
            strawberry_info_name=strawberry_info_name,
        )

        AddImportsVisitor.add_needed_import(self.context, "strawberry")
        RemoveImportsVisitor.remove_unused_import(
            self.context, "graphql", "GraphQLResolveInfo"
        )
        RemoveImportsVisitor.remove_unused_import(
            self.context, "graphql.type", "GraphQLResolveInfo"
        )
        annotation_name = (
            get_full_name_for_node(parameter.annotation.annotation)
            if parameter.annotation
            else None
        )
        if annotation_name in self._graphql_info_imports:
            module_name, asname = self._graphql_info_imports[annotation_name]
            RemoveImportsVisitor.remove_unused_import(
                self.context,
                module_name,
                "GraphQLResolveInfo",
                asname=asname,
            )

        return updated_node.with_changes(params=updated_params, body=updated_body)

    def _extension_base_name(self, node: cst.BaseExpression) -> str | None:
        name = get_full_name_for_node(node)
        if name is None:
            return None
        if name in self._extension_base_names:
            return self._extension_base_names[name]

        for module_name in self._strawberry_module_names:
            if not name.startswith(f"{module_name}."):
                continue
            qualified_name = f"strawberry{name.removeprefix(module_name)}"
            module, _, class_name = qualified_name.rpartition(".")
            if class_name in _EXTENSION_BASES.get(module, ()):
                return class_name
        return None

    def _annotation_kind(self, annotation: cst.Annotation | None) -> str:
        if annotation is None:
            return "graphql"

        name = get_full_name_for_node(annotation.annotation)
        if name in self._strawberry_info_names:
            return "strawberry"
        if name in self._graphql_info_names or name in {
            "graphql.GraphQLResolveInfo",
            "graphql.type.GraphQLResolveInfo",
            "Any",
            "typing.Any",
            "object",
        }:
            return "graphql"
        if any(
            name == f"{module_name}.Info"
            for module_name in self._strawberry_module_names
        ):
            return "strawberry"
        return "unknown"

    @staticmethod
    def _find_info_parameter(params: cst.Parameters, position: int) -> cst.Param | None:
        parameters = [*params.posonly_params, *params.params, *params.kwonly_params]
        return next(
            (parameter for parameter in parameters if parameter.name.value == "info"),
            parameters[position] if len(parameters) > position else None,
        )

    @staticmethod
    def _replace_parameter(
        params: cst.Parameters,
        original: cst.Param,
        replacement: cst.Param,
    ) -> cst.Parameters:
        def replace(parameters: Sequence[cst.Param]) -> tuple[cst.Param, ...]:
            return tuple(
                replacement if parameter is original else parameter
                for parameter in parameters
            )

        return params.with_changes(
            posonly_params=replace(params.posonly_params),
            params=replace(params.params),
            kwonly_params=replace(params.kwonly_params),
        )

    @staticmethod
    def _add_raw_info_alias(
        body: cst.BaseSuite,
        *,
        original_info_name: str,
        strawberry_info_name: str,
    ) -> cst.BaseSuite:
        assignment = cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(cst.Name(original_info_name))],
                    value=cst.Attribute(
                        value=cst.Name(strawberry_info_name),
                        attr=cst.Name("_raw_info"),
                    ),
                )
            ]
        )

        if isinstance(body, cst.SimpleStatementSuite):
            return cst.IndentedBlock(
                body=[assignment, cst.SimpleStatementLine(body=body.body)]
            )

        assert isinstance(body, cst.IndentedBlock)
        statements = list(body.body)
        insertion_index = 1 if statements and _is_docstring(statements[0]) else 0
        statements.insert(insertion_index, assignment)
        return body.with_changes(body=statements)


def _is_docstring(statement: cst.BaseStatement) -> bool:
    return (
        isinstance(statement, cst.SimpleStatementLine)
        and len(statement.body) == 1
        and isinstance(statement.body[0], cst.Expr)
        and isinstance(
            statement.body[0].value, (cst.SimpleString, cst.ConcatenatedString)
        )
    )


__all__ = ["ConvertSchemaExtensionInfo"]

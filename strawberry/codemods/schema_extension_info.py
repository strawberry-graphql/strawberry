from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.helpers import get_full_name_for_node

if TYPE_CHECKING:
    from collections.abc import Sequence


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


class ConvertSchemaExtensionInfo(VisitorBasedCodemodCommand):
    DESCRIPTION = (
        "Opts SchemaExtension.resolve into strawberry.Info while preserving its "
        "existing graphql-core Info behavior."
    )

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self._schema_extension_names: set[str] = set()
        self._strawberry_info_names: set[str] = set()
        self._graphql_info_names: set[str] = {"GraphQLResolveInfo"}
        self._graphql_info_imports: dict[str, tuple[str, str | None]] = {}
        self._strawberry_module_names: set[str] = {"strawberry"}
        self._class_stack: list[bool] = []
        self._class_function_depths: list[int] = []
        self._function_depth = 0

    def visit_Import(self, node: cst.Import) -> None:  # noqa: N802
        for alias in node.names:
            imported_module = get_full_name_for_node(alias.name)
            if imported_module == "strawberry":
                self._strawberry_module_names.add(_imported_name(alias) or "strawberry")
            elif (
                imported_module
                in {
                    "strawberry.extensions",
                    "strawberry.extensions.base_extension",
                }
                and alias.asname
            ):
                imported_name = _imported_name(alias)
                if imported_name:
                    self._schema_extension_names.add(f"{imported_name}.SchemaExtension")

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:  # noqa: N802
        module_name = get_full_name_for_node(node.module) if node.module else None
        if isinstance(node.names, cst.ImportStar):
            return

        for alias in node.names:
            original_name = get_full_name_for_node(alias.name)
            imported_name = _imported_name(alias)
            if original_name is None or imported_name is None:
                continue

            if (
                module_name
                in {
                    "strawberry.extensions",
                    "strawberry.extensions.base_extension",
                }
                and original_name == "SchemaExtension"
            ):
                self._schema_extension_names.add(imported_name)
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
        self._class_stack.append(
            any(self._is_schema_extension_base(base.value) for base in node.bases)
        )
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
        if (
            not self._class_stack
            or not self._class_stack[-1]
            or not is_direct_class_method
            or original_node.name.value != "resolve"
        ):
            return updated_node

        parameter = self._find_info_parameter(updated_node.params)
        if parameter is None:
            self.warn(
                "Skipped SchemaExtension.resolve because its info parameter "
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
        updated_body = self._add_raw_info_alias(
            updated_node.body,
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

    def _is_schema_extension_base(self, node: cst.BaseExpression) -> bool:
        name = get_full_name_for_node(node)
        if name is None:
            return False
        if name in self._schema_extension_names:
            return True
        return any(
            name == f"{module_name}.extensions.SchemaExtension"
            for module_name in self._strawberry_module_names
        )

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
    def _find_info_parameter(params: cst.Parameters) -> cst.Param | None:
        parameters = [*params.posonly_params, *params.params, *params.kwonly_params]
        return next(
            (parameter for parameter in parameters if parameter.name.value == "info"),
            parameters[3] if len(parameters) > 3 else None,
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

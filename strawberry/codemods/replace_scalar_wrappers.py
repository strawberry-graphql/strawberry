from __future__ import annotations

import libcst as cst
import libcst.matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor

# Mapping from old scalar wrapper names to their replacements
# Format: old_name -> (module, import_name, usage_name)
# If usage_name is None, it means we use module.import_name
SCALAR_REPLACEMENTS: dict[str, tuple[str, str, str | None]] = {
    "Date": ("datetime", "date", "datetime.date"),
    "DateTime": ("datetime", "datetime", "datetime.datetime"),
    "Time": ("datetime", "time", "datetime.time"),
    "Decimal": ("decimal", "Decimal", None),
    "UUID": ("uuid", "UUID", None),
}


class ReplaceScalarWrappers(VisitorBasedCodemodCommand):
    DESCRIPTION: str = (
        "Replaces deprecated scalar wrapper imports from "
        "strawberry.schema.types.base_scalars with their actual Python types. "
        "For example: Date -> datetime.date, UUID -> uuid.UUID"
    )
    METADATA_DEPENDENCIES = (cst.metadata.ParentNodeProvider,)

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        # Track which scalars are imported and need replacement
        self._imported_scalars: dict[str, str] = {}  # alias -> original_name

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:  # noqa: N802
        """Track imports from strawberry.schema.types.base_scalars."""
        if not m.matches(
            node,
            m.ImportFrom(
                module=m.Attribute(
                    value=m.Attribute(
                        value=m.Attribute(
                            value=m.Name("strawberry"),
                            attr=m.Name("schema"),
                        ),
                        attr=m.Name("types"),
                    ),
                    attr=m.Name("base_scalars"),
                )
            ),
        ):
            return True

        if isinstance(node.names, cst.ImportStar):
            return True

        for name in node.names:
            if isinstance(name, cst.ImportAlias):
                original_name = (
                    name.name.value if isinstance(name.name, cst.Name) else None
                )
                if original_name and original_name in SCALAR_REPLACEMENTS:
                    # Get the alias if present, otherwise use the original name
                    alias = (
                        name.asname.name.value
                        if name.asname and isinstance(name.asname.name, cst.Name)
                        else original_name
                    )
                    self._imported_scalars[alias] = original_name

        return True

    def leave_ImportFrom(  # noqa: N802
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom | cst.RemovalSentinel:
        """Remove or update imports from strawberry.schema.types.base_scalars."""
        if not m.matches(
            original_node,
            m.ImportFrom(
                module=m.Attribute(
                    value=m.Attribute(
                        value=m.Attribute(
                            value=m.Name("strawberry"),
                            attr=m.Name("schema"),
                        ),
                        attr=m.Name("types"),
                    ),
                    attr=m.Name("base_scalars"),
                )
            ),
        ):
            return updated_node

        if isinstance(original_node.names, cst.ImportStar):
            return updated_node

        # Filter out the scalar wrappers we're replacing
        remaining_names: list[cst.ImportAlias] = [
            name
            for name in original_node.names
            if (
                isinstance(name, cst.ImportAlias)
                and isinstance(name.name, cst.Name)
                and name.name.value not in SCALAR_REPLACEMENTS
            )
        ]

        # Add the replacement imports for all imported scalars
        for original_name in self._imported_scalars.values():
            module, import_name, usage_name = SCALAR_REPLACEMENTS[original_name]

            if usage_name and usage_name.startswith("datetime."):
                # For datetime types, we import the module
                AddImportsVisitor.add_needed_import(self.context, module)
            else:
                # For other types, we import the specific name
                AddImportsVisitor.add_needed_import(self.context, module, import_name)

        if not remaining_names:
            # Remove the entire import statement
            return cst.RemovalSentinel.REMOVE

        # Update the import to only include non-scalar names
        return updated_node.with_changes(
            names=remaining_names,
        )

    def leave_Name(  # noqa: N802
        self, original_node: cst.Name, updated_node: cst.Name
    ) -> cst.BaseExpression:
        """Replace usages of imported scalar wrappers with their actual types."""
        if original_node.value not in self._imported_scalars:
            return updated_node

        # Don't replace names that are part of import statements
        try:
            parent = self.get_metadata(cst.metadata.ParentNodeProvider, original_node)
            if isinstance(parent, (cst.ImportAlias, cst.AsName)):
                return updated_node
        except KeyError:
            pass

        original_name = self._imported_scalars[original_node.value]
        _module, import_name, usage_name = SCALAR_REPLACEMENTS[original_name]

        if usage_name:
            # Return module.name (e.g., datetime.date)
            parts = usage_name.split(".")
            if len(parts) == 2:
                return cst.Attribute(
                    value=cst.Name(parts[0]),
                    attr=cst.Name(parts[1]),
                )

        # Return just the name (e.g., UUID, Decimal)
        return cst.Name(import_name)

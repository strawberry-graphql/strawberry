from __future__ import annotations

import libcst as cst
import libcst.matchers as m
from libcst.codemod import VisitorBasedCodemodCommand


class ConvertStrawberryConfigToDict(VisitorBasedCodemodCommand):
    """Convert StrawberryConfig() instantiation to dict syntax.

    This codemod converts the deprecated class-based StrawberryConfig() syntax
    to the new dictionary syntax.

    Examples:
        # Before:
        config = StrawberryConfig()
        config = StrawberryConfig(auto_camel_case=True)

        # After:
        config = {}
        config = {"auto_camel_case": True}
    """

    DESCRIPTION: str = (
        "Converts StrawberryConfig() class instantiation to dictionary syntax"
    )

    def leave_Call(  # noqa: N802
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.BaseExpression:
        # Check if this is a StrawberryConfig() call
        if not self._is_strawberry_config_call(original_node):
            return updated_node

        # If no arguments, convert to empty dict {}
        if not original_node.args:
            return cst.Dict([])

        # Convert arguments to dict entries
        dict_elements = []
        for arg in original_node.args:
            # Only handle keyword arguments
            if arg.keyword is None:
                # Positional arguments not supported, skip this conversion
                return updated_node

            # Create dict key (string literal from keyword name)
            key = cst.SimpleString(f'"{arg.keyword.value}"')

            # Create dict value (the argument value)
            dict_elements.append(
                cst.DictElement(
                    key=key,
                    value=arg.value,
                )
            )

        # Return dictionary literal
        return cst.Dict(elements=dict_elements)

    def _is_strawberry_config_call(self, node: cst.Call) -> bool:
        """Check if this is a call to StrawberryConfig."""
        # Check for direct StrawberryConfig() call
        if m.matches(node.func, m.Name("StrawberryConfig")):
            return True

        # Check for strawberry.schema.config.StrawberryConfig()
        if m.matches(
            node.func,
            m.Attribute(
                value=m.Attribute(
                    value=m.Attribute(
                        value=m.Name("strawberry"),
                        attr=m.Name("schema"),
                    ),
                    attr=m.Name("config"),
                ),
                attr=m.Name("StrawberryConfig"),
            ),
        ):
            return True

        # Check for config.StrawberryConfig()
        return m.matches(
            node.func,
            m.Attribute(
                attr=m.Name("StrawberryConfig"),
            ),
        )
